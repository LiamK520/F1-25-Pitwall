from api.schemas import *
from state.live import MatchedLiveFrame
from state import CarState, ApplicationState
from udp.car_telemetry import CarTelemetryData
from udp.lap_data import LapData
from udp.session import SessionPacket
from udp.motion import MotionPacket, CarMotionData
from track import TrackGeometry

from state.enums import enum_label, TrackId, SessionType, Weather, SafetyCarStatus

# using custom serailiser to deal with nested structsures like car.participant.etc
def serialise_car(car: CarState) -> CarStateResponse:
    return CarStateResponse(
        index=car.index,
        name=car.participant.name if car.participant is not None else None,
        driver_id= car.participant.driver_id if car.participant is not None else None,
        race_number=car.participant.race_number if car.participant is not None else None,
        team_id=car.participant.team_id if car.participant is not None else None,
        position=car.lap.car_position if car.lap is not None else None,
        lap=car.lap.current_lap_num if car.lap is not None else None,
        sector=car.lap.sector if car.lap is not None else None,
        lap_distance=car.lap.lap_distance if car.lap is not None else None,
        result_status=car.lap.result_status if car.lap is not None else None,
        gear=car.telemetry.gear if car.telemetry is not None else None,
        speed=car.telemetry.speed if car.telemetry is not None else None,
        rpm=car.telemetry.engine_rpm if car.telemetry is not None else None
    )


def serialise_state(state: ApplicationState) -> StateResponse:
    session = state.session

    return StateResponse(
        session_uid=state.session_uid,

        track_id=session.track_id if session is not None else None,
        track_name=enum_label(
            TrackId,
            session.track_id if session is not None else None,
        ),

        session_type=session.session_type if session is not None else None,
        session_name=enum_label(
            SessionType,
            session.session_type if session is not None else None,
        ),

        total_laps=session.total_laps if session is not None else None,

        weather=session.weather if session is not None else None,
        weather_name=enum_label(
            Weather,
            session.weather if session is not None else None,
        ),

        track_temperature=(
            session.track_temperature if session is not None else None
        ),

        air_temperature=(
            session.air_temperature if session is not None else None
        ),

        safety_car_status=(
            session.safety_car_status if session is not None else None
        ),

        safety_car_status_name=enum_label(
            SafetyCarStatus,
            session.safety_car_status if session is not None else None,
        ),

        num_active_cars=state.num_active_cars,
        player_car_index=state.player_car_index,

        cars=[serialise_car(car) for car in state.cars],
    )


def serialise_session_update(session: SessionPacket) -> SessionUpdateResponse:
    """
    Serialise session packet using fields that update
    """

    return SessionUpdateResponse(
        session_uid=session.header.session_uid,
        weather=session.weather,
        weather_name=enum_label(Weather, session.weather),
        track_temperature=session.track_temperature,
        air_temperature=session.air_temperature,
        safety_car_status=session.safety_car_status,
        safety_car_status_name=enum_label(SafetyCarStatus, session.safety_car_status)
    )   


def _time_parts_to_ms(ms_part: int, minutes_part: int) -> int:
    """
    Combine F1 UDP minute/millisecond time fields into milliseconds.
    """
    return (minutes_part * 60_000) + ms_part


def serialise_live_car(
    index: int,
    lap: LapData,
    telemetry: CarTelemetryData,
) -> LiveCarResponse:
    """
    Serialise aligned LapData and CarTelemetryData for one car
    """

    return LiveCarResponse(
        index=index,

        # lap and timing
        last_lap_time_ms=lap.last_lap_time_ms,
        current_lap_time_ms=lap.current_lap_time_ms,

        sector1_time_ms=_time_parts_to_ms(
            lap.sector1_time_ms_part,
            lap.sector1_time_minutes_part,
        ),

        sector2_time_ms=_time_parts_to_ms(
            lap.sector2_time_ms_part,
            lap.sector2_time_minutes_part,
        ),

        delta_to_car_in_front_ms=_time_parts_to_ms(
            lap.delta_to_car_in_front_ms_part,
            lap.delta_to_car_in_front_minutes_part,
        ),

        delta_to_race_leader_ms=_time_parts_to_ms(
            lap.delta_to_race_leader_ms_part,
            lap.delta_to_race_leader_minutes_part,
        ),

        lap_distance=lap.lap_distance,
        total_distance=lap.total_distance,
        safety_car_delta=lap.safety_car_delta,

        position=lap.car_position,
        lap=lap.current_lap_num,
        pit_status=lap.pit_status,
        num_pit_stops=lap.num_pit_stops,
        sector=lap.sector,

        current_lap_invalid=bool(
            lap.current_lap_invalid
        ),

        penalties=lap.penalties,
        total_warnings=lap.total_warnings,
        corner_cutting_warnings=lap.corner_cutting_warnings,

        unserved_drive_throughs=(
            lap.num_unserved_drive_through_pens
        ),

        unserved_stop_go=(
            lap.num_unserved_stop_and_go_pens
        ),

        grid_position=lap.grid_position,
        driver_status=lap.driver_status,
        result_status=lap.result_status,

        pit_lane_timer_active=bool(
            lap.pit_lane_timer_active
        ),

        pit_lane_time_ms=lap.pit_lane_time_in_lane_ms,
        pit_stop_time_ms=lap.pit_stop_timer_ms,

        pit_stop_should_serve_penalty=bool(
            lap.pit_stop_should_serve_pen
        ),

        speed_trap_fastest_speed=lap.speed_trap_fastest_speed,

        speed_trap_fastest_lap=(
            None
            if lap.speed_trap_fastest_lap == 255
            else lap.speed_trap_fastest_lap
        ),

        # teleme
        speed=telemetry.speed,
        throttle=telemetry.throttle,
        steer=telemetry.steer,
        brake=telemetry.brake,
        clutch=telemetry.clutch,

        gear=telemetry.gear,
        rpm=telemetry.engine_rpm,
        drs=bool(telemetry.drs),

        rev_lights_percent=telemetry.rev_lights_percent,
        rev_lights_bit_value=telemetry.rev_lights_bit_value,

        brakes_temperature=telemetry.brakes_temperature,
        tyres_surface_temperature=telemetry.tyres_surface_temperature,
        tyres_inner_temperature=telemetry.tyres_inner_temperature,

        engine_temperature=telemetry.engine_temperature,

        tyres_pressure=telemetry.tyres_pressure,
        surface_type=telemetry.surface_type,
    )


def serialise_live_frame(live_frame: MatchedLiveFrame) -> LiveFrameResponse:
    lap_packet = live_frame.lap_data
    telemetry_packet = live_frame.telemetry

    header = lap_packet.header

    cars = [
        serialise_live_car(
            index=i,
            lap=lap_packet.cars[i],
            telemetry=telemetry_packet.cars[i],
        )
        for i in range(len(lap_packet.cars))
    ]

    return LiveFrameResponse(
        session_uid=header.session_uid,

        frame=header.frame_identifier,
        overall_frame=header.overall_frame_identifier,
        session_time=header.session_time,

        player_car_index=header.player_car_index,

        secondary_player_car_index=(
            None
            if header.secondary_player_car_index == 255
            else header.secondary_player_car_index
        ),

        time_trial_pb_car_index=(
            None
            if lap_packet.time_trial_pb_car_index == 255
            else lap_packet.time_trial_pb_car_index
        ),

        time_trial_rival_car_index=(
            None
            if lap_packet.time_trial_rival_car_index == 255
            else lap_packet.time_trial_rival_car_index
        ),

        mfd_panel_index=(
            None
            if telemetry_packet.mfd_panel_index == 255
            else telemetry_packet.mfd_panel_index
        ),

        mfd_panel_index_secondary_player=(
            None
            if telemetry_packet.mfd_panel_index_secondary_player == 255
            else telemetry_packet.mfd_panel_index_secondary_player
        ),

        suggested_gear=(
            None
            if telemetry_packet.suggested_gear == 0
            else telemetry_packet.suggested_gear
        ),

        cars=cars,
    )


def serialise_motion_car(index: int, motion: CarMotionData) -> MotionCarResponse:
    """
    serialise the motion values required to draw car on map
    """

    return MotionCarResponse(index=index, x=motion.world_position_x, 
                             z=motion.world_position_z, yaw=motion.yaw)


def serialise_motion_frame(packet: MotionPacket) -> MotionFrameResponse:
    """
    Serialise one frame of f1 motion containing all cars
    """

    header = packet.header

    cars = [serialise_motion_car(i, motion) for i, motion in enumerate(packet.cars)]

    return MotionFrameResponse(
        session_uid=header.session_uid,
        overall_frame=header.overall_frame_identifier,
        session_time=header.session_time,
        cars=cars
    )


def serialise_track_geometry(geometry: TrackGeometry) -> TrackGeometryResponse:
    return TrackGeometryResponse(
        track_id=geometry.track_id,
        track_length=geometry.track_length,

        min_x=geometry.min_x,
        max_x=geometry.max_x,
        min_z=geometry.min_z,
        max_z=geometry.max_z,

        sector_2_start=geometry.sector_2_start,
        sector_3_start=geometry.sector_3_start,
        marshal_zone_starts=geometry.marshal_zone_starts,

        points=[
            TrackPointResponse(
                distance=point.distance,
                x=point.x,
                z=point.z,
            )
            for point in geometry.points
        ]
    )