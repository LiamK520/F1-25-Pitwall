from dataclasses import dataclass, field

from udp.constants import NUM_CARS

# note only used for type hinting in private function. possibly remove import when finished
from udp.header import PacketHeader

from udp.motion import CarMotionData, MotionPacket
from udp.participants import ParticipantData,ParticipantsPacket
from udp.lap_data import LapData,LapDataPacket
from udp.car_telemetry import CarTelemetryData,CarTelemetryPacket
from udp.car_status import CarStatusData,CarStatusPacket
from udp.car_damage import CarDamageData,CarDamagePacket
from udp.session import SessionPacket
from udp.event import EventPacket, FlashbackEvent
from udp.session_history import SessionHistoryPacket
from udp.tyre_sets import TyreSetsPacket
from udp.car_setup import CarSetupData, CarSetupPacket
from udp.lap_positions import LapPositionsPacket
from udp.final_classification import FinalClassificationPacket

from state.history import LapTelemetry, LapTelemetryBuffer
from state.live import MatchedLiveFrame, FramePackets

from track import TrackBuilder, TrackMetadata

from statistics import median


@dataclass
class CarState:
    """
    Stores the current state for a single car. Each field holds the most recent value received from UDP data for that car.
    """
    index: int

    # live stuff

    participant: ParticipantData | None = None
    motion: CarMotionData | None = None
    lap: LapData | None = None
    telemetry: CarTelemetryData | None = None
    status: CarStatusData | None = None
    damage: CarDamageData | None = None
    setup: CarSetupData | None = None

    # history from udp
    session_history: SessionHistoryPacket | None = None
    tyre_sets: TyreSetsPacket | None = None

    # telem history
    current_lap_telemetry: LapTelemetryBuffer | None = None
    completed_lap_telemetry: dict[int, LapTelemetry] = field(default_factory=dict)


@dataclass
class ApplicationState:
    """
    Stores the latest state of the current session.

    Decoded UDP packets should be passed to update(), which uses their contents to update appropriate fields and keep the session state accurate.

    Note that state gets reset automatically if receiving a packet with a different session UID.
    """
    session_uid: int | None = None

    session: SessionPacket | None = None

    # automatically create all cars when we create state populate index for each
    cars: list[CarState] = field(
        default_factory=lambda: [CarState(index = i) for i in range(NUM_CARS)]
    )

    events: list[EventPacket] = field(default_factory=list)

    # position history
    # key is the lap history index, value is the position for all cars
    lap_positions: dict[int, tuple[int, ...]] = field(default_factory=dict)

    final_classification: FinalClassificationPacket | None = None

    num_active_cars: int = 0

    player_car_index: int | None = None
    # player only value
    next_front_wing_value: float | None = None

    # i dont know if i'll use this but keep for now
    secondary_player_car_index: int | None = None
    
    # packets with shared frame
    _frame_buffer: dict[int, FramePackets] = field(default_factory=dict)

    # flashback stuff
    _pending_flashback_time: float | None = None
    _pending_flashback_frame: int | None = None

    # latest matched lapdat and cartelem
    latest_live_frame: MatchedLiveFrame | None = None
    # same for motion
    latest_motion: MotionPacket | None = None

    track_builder: TrackBuilder | None = None

    # consts
    _MAX_FRAME_AGE = 10

    @property
    def player_car(self) -> CarState | None:
        if self.player_car_index is None:
            return None

        return self.cars[self.player_car_index]

    def reset(self, session_uid: int | None = None) -> None:
        """
        Clears current application state. This is used when a packet with a new session UID is recieved to wipe data from a previous session.
        """
        self.session_uid = session_uid

        self.session = None

        self.cars = [CarState(index = i) for i in range(NUM_CARS)]

        self.events.clear()
        self.num_active_cars = 0
        self.player_car_index = None
        self.secondary_player_car_index = None

        self.lap_positions.clear()
        self.final_classification = None
        self.next_front_wing_value = None

        self._frame_buffer.clear()

        self._pending_flashback_frame = None
        self._pending_flashback_time = None

        self.latest_live_frame = None
        self.latest_motion = None

        self.track_builder = None

    def update(self, packet) -> None:
        """
        Updates the state with the relevant information in the supplised packet
        """
        self._update_header(packet)

        if isinstance(packet, MotionPacket):
            self._update_motion(packet)

        elif isinstance(packet, ParticipantsPacket):
            self._update_participants(packet)

        elif isinstance(packet, LapDataPacket):
            self._update_lap_data(packet)

        elif isinstance(packet, CarTelemetryPacket):
            self._update_telemetry(packet)

        elif isinstance(packet, CarStatusPacket):
            self._update_status(packet)

        elif isinstance(packet, CarDamagePacket):
            self._update_damage(packet)

        elif isinstance(packet, SessionPacket):
            self._update_session(packet)

        elif isinstance(packet, EventPacket):
            self.events.append(packet)

            if packet.event_code == "FLBK":
                self._handle_flashback_event(packet)

        elif isinstance(packet, CarSetupPacket):
            self._update_setups(packet)

        elif isinstance(packet, SessionHistoryPacket):
            self._update_session_history(packet)

        elif isinstance(packet, TyreSetsPacket):
            self._update_tyre_sets(packet)

        elif isinstance(packet, LapPositionsPacket):
            self._update_lap_positions(packet)

        elif isinstance(packet, FinalClassificationPacket):
            self.final_classification = packet

    def _update_header(self, packet) -> None:
        """
        Update session and player information using packet header. A change in session UID indicates a new session, and the current state is reset.
        """
        header: PacketHeader = packet.header

        if self.session_uid is None:
            self.session_uid = header.session_uid

        # if uids dont match reset to new session
        elif header.session_uid != self.session_uid:
            self.reset(session_uid = header.session_uid)

        if header.player_car_index < NUM_CARS:
            self.player_car_index = header.player_car_index

        if header.secondary_player_car_index < NUM_CARS:
            self.secondary_player_car_index = header.secondary_player_car_index
        else:
            # set to none, as gt NUM_CARS signals no 2nd player
            self.secondary_player_car_index = None

    def _update_motion(self, packet: MotionPacket) -> None:
        self.latest_motion = packet

        for i, motion in enumerate(packet.cars):
            self.cars[i].motion = motion

        frame = packet.header.overall_frame_identifier

        # get frame packet if exists or make new
        frame_packets = self._frame_buffer.setdefault(frame, FramePackets())

        frame_packets.motion = packet

        self._try_process_frame(frame)
        self._clean_frame_buffer(frame)

    def _update_participants(self, packet: ParticipantsPacket):
        self.num_active_cars = packet.num_active_cars

        for i, part in enumerate(packet.participants):
            self.cars[i].participant = part

    def _update_lap_data(self, packet: LapDataPacket) -> None:
        pending_flashback = self._pending_flashback_time is not None

        for i, lap in enumerate(packet.cars):
            car = self.cars[i]

            # apply flashbacks only in lap data as we need the new lap number
            if pending_flashback:
                self._apply_flashback_to_car(car, target_lap_number=lap.current_lap_num, target_session_time=self._pending_flashback_time)

            self._update_lap_telemetry(car, lap)

            car.lap = lap

        if pending_flashback:
            # unset the flashback fields
            self._pending_flashback_time = None
            self._pending_flashback_frame = None

        frame = packet.header.overall_frame_identifier

        frame_packets = self._frame_buffer.setdefault(frame, FramePackets())

        frame_packets.lap_data = packet

        self._try_process_frame(frame)
        self._clean_frame_buffer(frame)

    def _update_telemetry(self, packet: CarTelemetryPacket) -> None:
        for i, telem in enumerate(packet.cars):
            car = self.cars[i]

            car.telemetry = telem

        frame = packet.header.overall_frame_identifier

        frame_packets = self._frame_buffer.setdefault(frame, FramePackets())

        frame_packets.telemetry = packet

        self._try_process_frame(frame)
        self._clean_frame_buffer(frame)

    def _update_status(self, packet: CarStatusPacket) -> None:
        for i, status in enumerate(packet.cars):
            self.cars[i].status = status

    def _update_damage(self, packet: CarDamagePacket) -> None:
        for i, dmg in enumerate(packet.cars):
            self.cars[i].damage = dmg

    def _update_session(self, packet: SessionPacket) -> None:
        self.session = packet

        if self.track_builder is None:
            metadata = TrackMetadata(
                track_id=packet.track_id,
                track_length=packet.track_length,
                sector_2_start=packet.sector2_lap_distance_start,
                sector_3_start=packet.sector3_lap_distance_start,
                # need to convert 0-1 scale to 0-track len
                marshal_zone_starts=tuple(
                    zone.zone_start * packet.track_length for zone in packet.marshal_zones
                )
            )
            self.track_builder = TrackBuilder(metadata)

    def _update_setups(self, packet: CarSetupPacket) -> None:
        for i, setup in enumerate(packet.car_setup_data):
            self.cars[i].setup = setup

        self.next_front_wing_value = packet.next_front_wing_value

    def _update_session_history(self, packet: SessionHistoryPacket) -> None:
        if packet.car_idx >= NUM_CARS:
            return

        self.cars[packet.car_idx].session_history = packet

    def _update_tyre_sets(self, packet: TyreSetsPacket) -> None:
        if packet.car_idx >= NUM_CARS:
            return

        self.cars[packet.car_idx].tyre_sets = packet

    def _update_lap_positions(self, packet: LapPositionsPacket) -> None:
        for i, pos in enumerate(packet.position_for_vehicle_idx):
            # get absolute index by adding lap start to current lap (i)
            # this allows storage of more than maximum number of laps in udp lap position
            lap_idx = packet.lap_start + i

            self.lap_positions[lap_idx] = pos


    def _try_process_frame(self, frame: int) -> None:
        """
        Tries to process the current frame using the packets it contains
        """

        frame_packets = self._frame_buffer.get(frame)

        # shouldn't happen but just in case
        if frame_packets is None:
            return

        # if we have lap data and telem, we can record telemetry
        if frame_packets.lap_data is not None and frame_packets.telemetry is not None and not frame_packets.live_processed:
            self._process_live_frame(frame_packets.lap_data, frame_packets.telemetry)
            frame_packets.live_processed = True

        # track stuff

        if self.track_builder is not None and frame_packets.lap_data is not None and frame_packets.motion is not None and not frame_packets.track_processed:
            self.track_builder.process_frame(frame_packets.lap_data, frame_packets.motion)

            frame_packets.track_processed = True

            # NOTE: terminal testing for now to see how coverage works out. appears to get to 100% after a single lap which is good
            # tomorrow investiage indiviual bins, bin density etc.
            if frame % 300 == 0:
                sample_counts = [count for count in self.track_builder.sample_counts() if count > 0]

                car_counts = [count for count in self.track_builder.car_counts() if count > 0]

                print(
                    f"Track samples: {len(self.track_builder.samples)} | "
                    f"Coverage: {self.track_builder.coverage():.1%} | "
                    f"Samples/bin min={min(sample_counts)} "
                    f"median={median(sample_counts):.1f} | "
                    f"Cars/bin min={min(car_counts)} "
                    f"median={median(car_counts):.1f} | "
                    f"5-car={self.track_builder.car_coverage(5):.1%} | "
                    f"10-car={self.track_builder.car_coverage(10):.1%} | "
                    f"15-car={self.track_builder.car_coverage(15):.1%} | "
                    f"20-car={self.track_builder.car_coverage(20):.1%}"
                )

    
    def _process_live_frame(self, lap_packet: LapDataPacket, telemetry_packet: CarTelemetryPacket) -> None:
        """
        process lap data and telemetry info that relate to the same frame
        """

        self.latest_live_frame = MatchedLiveFrame(lap_packet, telemetry_packet)

        for i in range(NUM_CARS):
            car = self.cars[i]

            lap = lap_packet.cars[i]
            telem = telemetry_packet.cars[i]

            time = telemetry_packet.header.session_time

            self._record_telemetry_sample(car, lap, telem, time)

    def _clean_frame_buffer(self, current_frame: int) -> None:
        """
        Throws away packets that unlikely to be aligned due to packet loss.

        Packets that are _MAX_FRAME_AGE (10) frames older or more than the current frame are discarded.
        """

        thresh = current_frame - self._MAX_FRAME_AGE

        # looping over keys is probably fine as buffer size should be max 10
        # in practice it'll probably be even smaller due to alignments

        for frame in list(self._frame_buffer):
            if frame <= thresh:
                del self._frame_buffer[frame]
        

    # TODO: flashback will need to be handled somehow. figure that out later
    def _record_telemetry_sample(self, car:CarState, lap: LapData, telemetry: CarTelemetryData, session_time: float) -> None:
        """Add a telemetry sample to the current buffer.
        
        The passed LapData and CarTelemetryData should be aligned (same frame number)
        """

        # lap buffer hasn't been made yet
        if car.current_lap_telemetry is None:
            return

        # guard to ensure we don't write into wrong lap
        if car.current_lap_telemetry.lap_number != lap.current_lap_num:
            return

        car.current_lap_telemetry.append(
            session_time=session_time,
            lap_distance=lap.lap_distance,
            speed=telemetry.speed,
            throttle=telemetry.throttle,
            brake=telemetry.brake,
            steer=telemetry.steer,
            gear=telemetry.gear,
            engine_rpm=telemetry.engine_rpm,
            drs=bool(telemetry.drs),
        )

    def _update_lap_telemetry(self, car: CarState, new_lap: LapData) -> None:
        """
        Starts/completes/replaces the telemetry buffer for a car's current lap.

        A higher new lap signals a completed lap and the telemetry is recorded. An unexpected (lower) new lap means we replace the current buffer
        without sving it to avoid incorrect record.
        """

        new_lap_number = new_lap.current_lap_num

        # no hist for before race
        if new_lap_number == 0:
            return

        if car.current_lap_telemetry is None:
            car.current_lap_telemetry = LapTelemetryBuffer(lap_number=new_lap_number)
            return

        current_lap_number = car.current_lap_telemetry.lap_number

        # still same lap do nothing
        if current_lap_number == new_lap_number:
            return

        # normal nice lap
        # for now don't consider strange gaps like 4 to 6
        if new_lap_number > current_lap_number:
            self._complete_lap_telemetry(car)

        # start new buffer for new lap
        # hopefully handles stuff like flashback
        car.current_lap_telemetry = LapTelemetryBuffer(new_lap_number)

    def _complete_lap_telemetry(self, car: CarState) -> None:
        """finalise car's current telemetry buffer into a complted lap"""

        buffer = car.current_lap_telemetry

        if buffer is None:
            return

        # useless data, nothin sampled
        if not buffer.lap_distance:
            return


        completed = buffer.finish()

        car.completed_lap_telemetry[buffer.lap_number] = completed


    def _handle_flashback_event(self, packet: EventPacket) -> None:
        flashback = packet.details

        # if this method is called the vent should always be Flashback
        assert isinstance(flashback, FlashbackEvent)

        self._pending_flashback_time = flashback.flashback_session_time
        self._pending_flashback_frame = flashback.flashback_frame_identifier

        # clear these as the old frames are uselss now
        self._frame_buffer.clear()
        self.latest_live_frame = None
        self.latest_motion = None


    def _apply_flashback_to_car(self, car: CarState, target_lap_number: int, target_session_time: float) -> None:
        buffer = car.current_lap_telemetry

        if buffer is None:
            # we dont need to do anything
            return

        # not sure if this can happen but dont want a buffer for pre-race
        if target_lap_number == 0:
            car.current_lap_telemetry = None
            return

        # same lap so trim current buffer
        if buffer.lap_number == target_lap_number:
            buffer.trim_after_session_time(target_session_time)
            return

        # earlier lap flashback
        if buffer.lap_number > target_lap_number:
            # get rid of everything after the lap we are on
            # i dont think flashbacks can cross more than one lap, but just to be safe (e.g. mods)
            for lap_number in list(car.completed_lap_telemetry):
                if lap_number > target_lap_number:
                    del car.completed_lap_telemetry[lap_number]

            # target lap that was previously finished
            target_lap = car.completed_lap_telemetry.pop(target_lap_number, None)

            if target_lap is None:
                # just make a fresh buffer as we have not got a record for this lap
                car.current_lap_telemetry = LapTelemetryBuffer(target_lap_number)
                return

            # otherwise we need to restore the buffer and trim
            new_buffer = target_lap.to_buffer()
            new_buffer.trim_after_session_time(target_session_time)

            car.current_lap_telemetry = new_buffer