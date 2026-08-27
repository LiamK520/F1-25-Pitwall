from types import SimpleNamespace

from api.schemas import CarStateResponse, StateResponse, SessionUpdateResponse
from api.serialiser import serialise_car, serialise_live_car, serialise_live_frame, serialise_state, serialise_session_update
from state.application_state import ApplicationState, CarState
from udp.constants import NUM_CARS
from state.live import MatchedLiveFrame

def test_serialise_empty_state():
    """
    Tests that empty application state still creates a state response
    """
    state = ApplicationState()

    response = serialise_state(state)

    assert isinstance(response, StateResponse)

    assert response.session_uid is None
    assert response.track_id is None
    assert response.session_type is None

    assert response.total_laps is None
    assert response.weather is None
    assert response.track_temperature is None
    assert response.air_temperature is None
    assert response.safety_car_status is None

    assert response.track_name == None
    assert response.session_name == None
    assert response.weather_name == None
    assert response.safety_car_status_name == None

    assert response.num_active_cars == 0
    assert response.player_car_index is None

    assert len(response.cars) == NUM_CARS

    for i, car in enumerate(response.cars):
        assert car.index == i

        assert car.name is None
        assert car.driver_id is None
        assert car.race_number is None
        assert car.team_id is None

        assert car.position is None
        assert car.lap is None
        assert car.sector is None
        assert car.lap_distance is None
        assert car.result_status is None

        assert car.speed is None
        assert car.gear is None
        assert car.rpm is None


def test_serialise_car():
    car = CarState(7)

    # simple napmespace is fine as packet handling already tested
    car.participant = SimpleNamespace(name="NORRIS", driver_id=54, race_number=4, team_id=8)

    car.lap = SimpleNamespace(car_position=2, current_lap_num=12, sector=1, lap_distance=1100.0, result_status=2)

    car.telemetry = SimpleNamespace(speed=287, gear=7, engine_rpm=11520)

    response = serialise_car(car)

    assert isinstance(response, CarStateResponse)

    assert response.index == 7

    assert response.name == "NORRIS"
    assert response.driver_id == 54
    assert response.race_number == 4
    assert response.team_id == 8

    assert response.position == 2
    assert response.lap == 12
    assert response.sector == 1
    assert response.lap_distance == 1100.0
    assert response.result_status == 2

    assert response.speed == 287
    assert response.gear == 7
    assert response.rpm == 11520


def test_serialise_state():
    state = ApplicationState()

    state.session_uid = 123456789
    state.num_active_cars = 20
    state.player_car_index = 19

    state.session = SimpleNamespace(
        track_id=2,
        session_type=15,
        total_laps=52,
        weather=0,
        track_temperature=31,
        air_temperature=22,
        safety_car_status=0,
    )

    # test one car also
    car = state.cars[5]

    car.participant = SimpleNamespace(name="LECLERC", driver_id=58, race_number=16, team_id=1)

    car.lap = SimpleNamespace(car_position=3, current_lap_num=4, sector=2, lap_distance=4100.0, result_status=2)

    car.telemetry = SimpleNamespace(speed=301, gear=8, engine_rpm=11900)

    response = serialise_state(state)

    assert isinstance(response, StateResponse)

    assert response.session_uid == 123456789
    assert response.track_id == 2
    assert response.session_type == 15

    assert response.total_laps == 52
    assert response.weather == 0
    assert response.track_temperature == 31
    assert response.air_temperature == 22
    assert response.safety_car_status == 0

    assert response.track_name == "Shanghai"
    assert response.session_name == "Race"
    assert response.weather_name == "Clear"
    assert response.safety_car_status_name == "None"

    assert response.num_active_cars == 20
    assert response.player_car_index == 19

    assert len(response.cars) == NUM_CARS
    assert [car.index for car in response.cars] == list(range(NUM_CARS))

    car_response = response.cars[5]

    assert car_response.index == 5
    assert car_response.name == "LECLERC"
    assert car_response.race_number == 16
    assert car_response.position == 3
    assert car_response.lap == 4
    assert car_response.speed == 301


def test_serialise_live_car():
    lap = SimpleNamespace(
        last_lap_time_ms=91_234,
        current_lap_time_ms=45_678,

        sector1_time_ms_part=23_456,
        sector1_time_minutes_part=0,
        sector2_time_ms_part=12_345,
        sector2_time_minutes_part=1,

        delta_to_car_in_front_ms_part=1_234,
        delta_to_car_in_front_minutes_part=0,
        delta_to_race_leader_ms_part=5_678,
        delta_to_race_leader_minutes_part=0,

        lap_distance=2345.5,
        total_distance=12_345.5,
        safety_car_delta=0.75,

        car_position=4,
        current_lap_num=7,
        pit_status=0,
        num_pit_stops=1,
        sector=1,

        current_lap_invalid=0,

        penalties=5,
        total_warnings=2,
        corner_cutting_warnings=1,

        num_unserved_drive_through_pens=1,
        num_unserved_stop_and_go_pens=2,

        grid_position=6,
        driver_status=4,
        result_status=2,

        pit_lane_timer_active=0,
        pit_lane_time_in_lane_ms=0,
        pit_stop_timer_ms=0,
        pit_stop_should_serve_pen=0,

        speed_trap_fastest_speed=321.5,
        speed_trap_fastest_lap=6,
    )

    telemetry = SimpleNamespace(
        speed=287,
        throttle=0.91,
        steer=-0.12,
        brake=0.0,
        clutch=0,

        gear=7,
        engine_rpm=11_500,
        drs=1,

        rev_lights_percent=87,
        rev_lights_bit_value=12345,

        brakes_temperature=(600, 610, 620, 630),
        tyres_surface_temperature=(95, 96, 97, 98),
        tyres_inner_temperature=(90, 91, 92, 93),

        engine_temperature=105,

        tyres_pressure=(22.5, 22.6, 23.0, 23.1),
        surface_type=(0, 0, 0, 0),
    )

    response = serialise_live_car(index=3,lap=lap,telemetry=telemetry)

    assert response.index == 3

    assert response.position == 4
    assert response.lap == 7
    assert response.sector == 1

    assert response.sector1_time_ms == 23_456
    assert response.sector2_time_ms == 72_345

    assert response.delta_to_car_in_front_ms == 1_234
    assert response.delta_to_race_leader_ms == 5_678

    assert response.speed == 287
    assert response.throttle == 0.91
    assert response.gear == 7
    assert response.rpm == 11_500
    assert response.drs is True

    assert response.brakes_temperature == (600, 610, 620, 630)
    assert response.tyres_pressure == (22.5, 22.6, 23.0, 23.1)


def test_serialise_live_frame():
    header = SimpleNamespace(
        session_uid=123456,
        session_time=42.5,
        frame_identifier=500,
        overall_frame_identifier=700,
        player_car_index=3,
        secondary_player_car_index=255,
    )

    lap = SimpleNamespace(
        last_lap_time_ms=90_000,
        current_lap_time_ms=45_000,

        sector1_time_ms_part=20_000,
        sector1_time_minutes_part=0,
        sector2_time_ms_part=40_000,
        sector2_time_minutes_part=0,

        delta_to_car_in_front_ms_part=500,
        delta_to_car_in_front_minutes_part=0,
        delta_to_race_leader_ms_part=2_500,
        delta_to_race_leader_minutes_part=0,

        lap_distance=2000.0,
        total_distance=10_000.0,
        safety_car_delta=0.0,

        car_position=2,
        current_lap_num=5,
        pit_status=0,
        num_pit_stops=0,
        sector=1,

        current_lap_invalid=0,

        penalties=0,
        total_warnings=0,
        corner_cutting_warnings=0,

        num_unserved_drive_through_pens=0,
        num_unserved_stop_and_go_pens=0,

        grid_position=4,
        driver_status=4,
        result_status=2,

        pit_lane_timer_active=0,
        pit_lane_time_in_lane_ms=0,
        pit_stop_timer_ms=0,
        pit_stop_should_serve_pen=0,

        speed_trap_fastest_speed=315.0,
        speed_trap_fastest_lap=255,
    )

    telemetry = SimpleNamespace(
        speed=250,
        throttle=1.0,
        steer=0.0,
        brake=0.0,
        clutch=0,

        gear=6,
        engine_rpm=10_500,
        drs=0,

        rev_lights_percent=70,
        rev_lights_bit_value=100,

        brakes_temperature=(500, 500, 500, 500),
        tyres_surface_temperature=(90, 90, 90, 90),
        tyres_inner_temperature=(85, 85, 85, 85),

        engine_temperature=100,

        tyres_pressure=(22.0, 22.0, 22.0, 22.0),
        surface_type=(0, 0, 0, 0),
    )

    lap_packet = SimpleNamespace( header=header, cars=(lap,), time_trial_pb_car_index=255, time_trial_rival_car_index=255)

    telemetry_packet = SimpleNamespace( header=header, cars=(telemetry,), mfd_panel_index=255, mfd_panel_index_secondary_player=255, suggested_gear=0)

    matched = MatchedLiveFrame( lap_data=lap_packet, telemetry=telemetry_packet)

    response = serialise_live_frame(matched)

    assert response.type == "live_frame"

    assert response.session_uid == 123456
    assert response.frame == 500
    assert response.overall_frame == 700
    assert response.session_time == 42.5

    assert response.player_car_index == 3
    assert response.secondary_player_car_index is None

    assert response.time_trial_pb_car_index is None
    assert response.time_trial_rival_car_index is None

    assert response.mfd_panel_index is None
    assert response.mfd_panel_index_secondary_player is None
    assert response.suggested_gear is None

    assert len(response.cars) == 1

    car = response.cars[0]

    assert car.index == 0
    assert car.position == 2
    assert car.speed == 250

    # 255 means fastest-lap value has not been set
    assert car.speed_trap_fastest_lap is None


def test_serialise_session_update():
    session = SimpleNamespace(
        header=SimpleNamespace(session_uid=123456789),

        weather=0,
        track_temperature=34,
        air_temperature=23,

        safety_car_status=0
    )

    response = serialise_session_update(session)

    assert isinstance(response, SessionUpdateResponse)

    assert response.type == "session_update"
    assert response.session_uid == 123456789

    assert response.weather == 0
    assert response.weather_name == "Clear"

    assert response.track_temperature == 34
    assert response.air_temperature == 23

    assert response.safety_car_status == 0
    assert response.safety_car_status_name == "None"