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


@dataclass
class CarState:
    """
    Stores the current state for a single car. Each field holds the most recent value received from UDP data for that car.
    """
    index: int

    participant: ParticipantData | None = None
    motion: CarMotionData | None = None
    lap: LapData | None = None
    telemetry: CarTelemetryData | None = None
    status: CarStatusData | None = None
    damage: CarDamageData | None = None


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

    num_active_cars: int = 0

    player_car_index: int | None = None
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
            self.cars[i].lap = lap

    def _update_telemetry(self, packet: CarTelemetryPacket) -> None:
        for i, telem in enumerate(packet.cars):
            self.cars[i].telemetry = telem

    def _update_status(self, packet: CarStatusPacket) -> None:
        for i, status in enumerate(packet.cars):
            self.cars[i].status = status

    def _update_damage(self, packet: CarDamagePacket) -> None:
        for i, dmg in enumerate(packet.cars):
            self.cars[i].damage = dmg