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
from udp.event import EventPacket
from udp.session_history import SessionHistoryPacket
from udp.tyre_sets import TyreSetsPacket
from udp.car_setup import CarSetupData, CarSetupPacket
from udp.lap_positions import LapPositionsPacket
from udp.final_classification import FinalClassificationPacket

from state.history import LapTelemetry, LapTelemetryBuffer


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
            self.session = packet

        elif isinstance(packet, EventPacket):
            self.events.append(packet)

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
        for i, motion in enumerate(packet.cars):
            self.cars[i].motion = motion

    def _update_participants(self, packet: ParticipantsPacket):
        self.num_active_cars = packet.num_active_cars

        for i, part in enumerate(packet.participants):
            self.cars[i].participant = part

    def _update_lap_data(self, packet: LapDataPacket) -> None:
        for i, lap in enumerate(packet.cars):
            car = self.cars[i]

            self._update_lap_telemetry(car, lap)

            car.lap = lap

    def _update_telemetry(self, packet: CarTelemetryPacket) -> None:
        for i, telem in enumerate(packet.cars):
            car = self.cars[i]

            car.telemetry = telem

            self._record_telemetry_sample(car=car, telemetry=telem, session_time=packet.header.session_time)

    def _update_status(self, packet: CarStatusPacket) -> None:
        for i, status in enumerate(packet.cars):
            self.cars[i].status = status

    def _update_damage(self, packet: CarDamagePacket) -> None:
        for i, dmg in enumerate(packet.cars):
            self.cars[i].damage = dmg

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

    # TODO: flashback will need to be handled somehow. figure that out later
    def _record_telemetry_sample(self, car:CarState, telemetry: CarTelemetryData, session_time: float) -> None:
        """add a telemetry sample to the current buffer"""

        if car.lap is None:
            return

        if car.current_lap_telemetry is None:
            return

        # guard to ensure we don't write into wrong lap
        if car.current_lap_telemetry.lap_number != car.lap.current_lap_num:
            return

        car.current_lap_telemetry.append(
            session_time=session_time,
            lap_distance=car.lap.lap_distance,
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

        car.completed_laps_history[buffer.lap_number] = completed