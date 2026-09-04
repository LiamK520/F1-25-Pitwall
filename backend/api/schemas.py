from pydantic import BaseModel
from typing import Literal


# static api responses

class CarStateResponse(BaseModel):
    """
    Represents a snapshot of a car that is used in StateResponse
    """
    index: int

    name: str | None
    driver_id: int | None
    race_number: int | None
    team_id: int | None

    position: int | None
    lap: int | None
    sector: int | None
    lap_distance: float | None
    result_status: int | None

    speed: int | None
    gear: int | None
    rpm: int | None


class StateResponse(BaseModel):
    """
    Represents a broad snapshot that contains many important information about the current session. It contains no live data.

    This is designed to be accessed via a HTTP request. This will not be used for frequent data access.
    """
    session_uid: int | None

    track_id: int | None
    track_name: str | None

    session_type: int | None
    session_name: str | None

    total_laps: int | None

    weather: int | None
    weather_name: str | None

    track_temperature: int | None
    air_temperature: int | None

    safety_car_status: int | None
    safety_car_status_name: str | None

    num_active_cars: int
    player_car_index: int | None

    cars: list[CarStateResponse]


class SessionUpdateResponse(BaseModel):
    """
    Stores session data that typically changes slowly over time. Similar to StateResponse but excludes fixed fields like track
    """

    type: Literal["session_update"] = "session_update"

    # use as identifier
    session_uid: int

    weather: int
    weather_name: str

    track_temperature: int
    air_temperature: int

    safety_car_status: int
    safety_car_status_name: str


# websocket stuff

class LiveCarResponse(BaseModel):
    """
    Frame-aligned live timing and telemetry for one car.
    """

    index: int

    # lap tim info
    last_lap_time_ms: int
    current_lap_time_ms: int

    sector1_time_ms: int
    sector2_time_ms: int

    delta_to_car_in_front_ms: int
    delta_to_race_leader_ms: int

    lap_distance: float
    total_distance: float
    safety_car_delta: float

    position: int
    lap: int
    pit_status: int
    num_pit_stops: int
    sector: int

    current_lap_invalid: bool

    penalties: int
    total_warnings: int
    corner_cutting_warnings: int
    unserved_drive_throughs: int
    unserved_stop_go: int

    grid_position: int
    driver_status: int
    result_status: int

    pit_lane_timer_active: bool
    pit_lane_time_ms: int
    pit_stop_time_ms: int
    pit_stop_should_serve_penalty: bool

    speed_trap_fastest_speed: float
    speed_trap_fastest_lap: int | None

    # telem
    speed: int
    throttle: float
    steer: float
    brake: float
    clutch: int

    gear: int
    rpm: int
    drs: bool

    rev_lights_percent: int
    rev_lights_bit_value: int

    # wheels rl rr fl fr
    brakes_temperature: tuple[int, int, int, int]
    tyres_surface_temperature: tuple[int, int, int, int]
    tyres_inner_temperature: tuple[int, int, int, int]

    engine_temperature: int

    tyres_pressure: tuple[float, float, float, float]
    surface_type: tuple[int, int, int, int]


class LiveFrameResponse(BaseModel):
    """
    One coherent live frame created from frame-aligned
    LapData and CarTelemetry packets.
    """

    # type might be useful later probably send multiple msg types
    type: Literal["live_frame"] = "live_frame"

    session_uid: int

    frame: int
    overall_frame: int
    session_time: float

    player_car_index: int
    secondary_player_car_index: int | None

    # lapdata tt ref
    time_trial_pb_car_index: int | None
    time_trial_rival_car_index: int | None

    # telemetry player values
    mfd_panel_index: int | None
    mfd_panel_index_secondary_player: int | None
    suggested_gear: int | None

    cars: list[LiveCarResponse]


class MotionCarResponse(BaseModel):
    """
    Position and direction of a car
    """
    index: int

    # skipping y as probably don't need altitude in track map
    x: float
    z: float

    # direction for 2d map (unsure if will be used)
    yaw: float


class MotionFrameResponse(BaseModel):
    """
    Motion data for a frame containing all car
    """

    type: Literal["motion_frame"] = "motion_frame"

    session_uid: int

    overall_frame: int
    session_time: float

    cars: list[MotionCarResponse]


class TrackPointResponse(BaseModel):
    distance: float
    x: float
    z: float


class TrackGeometryResponse(BaseModel):
    track_id: int
    track_length: int

    min_x: float
    max_x: float
    min_z: float
    max_z: float

    sector_2_start: float
    sector_3_start: float
    marshal_zone_starts: tuple[float, ...]

    points: list[TrackPointResponse]


class TrackReadyResponse(BaseModel):
    type: Literal["track_ready"] = "track_ready"

    session_uid: int
    track_id: int


class LapTelemetryResponse(BaseModel):
    """
    telemetry samples for one lap for one car
    """

    car_index: int
    lap_number: int

    session_time: list[float]
    lap_distance: list[float]

    speed: list[int]
    throttle: list[float]
    brake: list[float]
    steer: list[float]

    gear: list[int]
    rpm: list[int]

    drs: list[bool]


class AvailableLapsResponse(BaseModel):
    car_index: int
    laps: list[int]