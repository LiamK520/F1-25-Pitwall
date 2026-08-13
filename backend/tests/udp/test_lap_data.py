import struct

import pytest

from udp.lap_data import LAP_DATA_SIZE, LAP_DATA_PACKET_SIZE, LapData, LapDataPacket
from tests.helpers import make_header
from udp.packet_id import PacketId
from udp.constants import NUM_CARS

LAP_DATA_FORMAT = "<IIHBHBHBHBfff15BHHBfB"

def make_lap_data(
    car_position: int = 1,
    current_lap_num: int = 5,
    lap_distance: float = 2500.0,
) -> bytes:
    return struct.pack(
        LAP_DATA_FORMAT,
        91234,          # last_lap_time_ms
        45123,          # current_lap_time_ms

        30250,          # sector1_time_ms_part
        0,              # sector1_time_minutes_part

        29800,          # sector2_time_ms_part
        0,              # sector2_time_minutes_part

        1250,           # delta_to_car_in_front_ms_part
        0,              # delta_to_car_in_front_minutes_part

        3500,           # delta_to_race_leader_ms_part
        0,              # delta_to_race_leader_minutes_part

        lap_distance,
        12000.0,        # total_distance
        0.0,            # safety_car_delta

        car_position,
        current_lap_num,
        0,              # pit_status
        1,              # num_pit_stops
        1,              # sector - sector 2
        0,              # current_lap_invalid
        5,              # penalties
        2,              # total_warnings
        1,              # corner_cutting_warnings
        0,              # unserved drive-throughs
        0,              # unserved stop-go
        3,              # grid_position
        4,              # driver_status - on track
        2,              # result_status - active
        0,              # pit_lane_timer_active

        0,              # pit_lane_time_in_lane_ms
        2450,           # pit_stop_timer_ms
        0,              # pit_stop_should_serve_pen

        327.5,          # speed_trap_fastest_speed
        4,              # speed_trap_fastest_lap
    )


def make_lap_data_packet() -> bytes:
    data = make_header(PacketId.LAP_DATA)

    for i in range(NUM_CARS):
        data += make_lap_data(
            car_position=i + 1,
            current_lap_num=5,
            lap_distance=2000.0 + i,
        )

    # Time Trial PB and rival indexes
    data += struct.pack("<BB", 255, 255)

    return data


def test_lap_data_size():
    assert LAP_DATA_SIZE == 57

def test_lap_data_packet_size():
    assert LAP_DATA_PACKET_SIZE == 1285


def test_lap_data_read():
    data = make_lap_data(car_position=3, current_lap_num=7, lap_distance=3456.5)

    lap = LapData.from_bytes(data, 0)

    assert lap.last_lap_time_ms == 91234
    assert lap.current_lap_time_ms == 45123

    assert lap.car_position == 3
    assert lap.current_lap_num == 7

    assert lap.lap_distance == 3456.5

    assert lap.pit_status == 0
    assert lap.num_pit_stops == 1
    assert lap.sector == 1

    assert lap.penalties == 5
    assert lap.total_warnings == 2

    assert lap.driver_status == 4
    assert lap.result_status == 2

    assert lap.speed_trap_fastest_speed == 327.5
    assert lap.speed_trap_fastest_lap == 4


def test_lap_data_packet_read():
    data = make_lap_data_packet()

    packet = LapDataPacket.from_bytes(data)

    assert packet.header.packet_id == PacketId.LAP_DATA
    assert len(packet.cars) == 22

    assert packet.cars[0].car_position == 1
    assert packet.cars[0].lap_distance == 2000.0

    assert packet.cars[5].car_position == 6
    assert packet.cars[5].lap_distance == 2005.0

    assert packet.cars[21].car_position == 22
    assert packet.cars[21].lap_distance == 2021.0

    assert packet.time_trial_pb_car_index == 255
    assert packet.time_trial_rival_car_index == 255


def test_lap_data_packet_wrong_size():
    data = bytes(100)

    with pytest.raises(ValueError):
        LapDataPacket.from_bytes(data) 