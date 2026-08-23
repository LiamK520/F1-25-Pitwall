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

    track_id : int | None
    session_type: int | None

    num_active_cars: int
    player_car_index: int | None

    cars: list[CarStateResponse]



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

    # wheels rr rl lr ll
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
    index: int

    world_position_x: float
    world_position_y: float
    world_position_z: float

    world_velocity_x: float
    world_velocity_y: float
    world_velocity_z: float

    world_forward_dir_x: int
    world_forward_dir_y: int
    world_forward_dir_z: int

    world_right_dir_x: int
    world_right_dir_y: int
    world_right_dir_z: int

    g_force_lateral: float
    g_force_longitudinal: float
    g_force_vertical: float

    yaw: float
    pitch: float
    roll: float