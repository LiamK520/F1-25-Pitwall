import struct

import pytest

from tests.helpers import make_header

from udp.constants import NUM_CARS
from udp.header import HEADER_SIZE
from udp.lap_positions import LAP_POSITIONS_PACKET_SIZE, LAP_POSITIONS_STRUCT, MAX_NUM_LAPS_IN_LAP_POSITIONS_HISTORY_PACKET,LapPositionsPacket
from udp.packet_id import PacketId


def make_lap_positions_packet(
    num_laps: int = 3,
    lap_start: int = 0,
) -> bytes:

    data = make_header(
        PacketId.LAP_POSITIONS,
        player_car_index=0,
    )

    data += struct.pack(
        "<BB",
        num_laps,
        lap_start,
    )

    row_0 = list(range(1, NUM_CARS + 1))

    # reversed so that any error accessing row/col is detected better
    row_1 = list(range(NUM_CARS, 0, -1))

    # contains 0 to test unrecord lap
    row_2 = [0,5,10,15] + [1] * (NUM_CARS - 4)

    rows = [row_0,row_1,row_2]

    # udp packet always contains max rows
    for i in range(MAX_NUM_LAPS_IN_LAP_POSITIONS_HISTORY_PACKET):
        if i < len(rows):
            row = rows[i]
        else:
            row = [0] * NUM_CARS

        data += bytes(row)

    return data


def test_lap_positions_struct_size():
    assert HEADER_SIZE + LAP_POSITIONS_STRUCT.size == LAP_POSITIONS_PACKET_SIZE


def test_lap_positions_packet_size():
    data = make_lap_positions_packet()

    assert len(data) == LAP_POSITIONS_PACKET_SIZE


def test_lap_positions_decodes_header_fields():
    packet = LapPositionsPacket.from_bytes(make_lap_positions_packet(num_laps=3, lap_start=50))

    assert packet.num_laps == 3
    assert packet.lap_start == 50


def test_lap_positions_decodes_first_lap():
    packet = LapPositionsPacket.from_bytes(make_lap_positions_packet())

    first_lap = packet.position_for_vehicle_idx[0]

    assert len(first_lap) == NUM_CARS

    assert first_lap[0] == 1
    assert first_lap[1] == 2
    assert first_lap[10] == 11
    assert first_lap[21] == 22


def test_lap_positions_decodes_multiple_laps_correctly():
    packet = LapPositionsPacket.from_bytes(make_lap_positions_packet())

    first_lap = packet.position_for_vehicle_idx[0]
    second_lap = packet.position_for_vehicle_idx[1]

    assert first_lap[0] == 1
    assert first_lap[21] == 22

    assert second_lap[0] == 22
    assert second_lap[21] == 1


def test_lap_positions_preserves_zero_position():
    packet = LapPositionsPacket.from_bytes(make_lap_positions_packet())

    third_lap = packet.position_for_vehicle_idx[2]

    assert third_lap[0] == 0
    assert third_lap[1] == 5
    assert third_lap[2] == 10
    assert third_lap[3] == 15


def test_lap_positions_only_stores_num_laps():
    packet = LapPositionsPacket.from_bytes(make_lap_positions_packet(num_laps=2))

    assert len(packet.position_for_vehicle_idx) == 2


def test_lap_positions_rejects_wrong_packet_size():
    data = make_lap_positions_packet()

    with pytest.raises(ValueError):
        LapPositionsPacket.from_bytes(data[:-1])


def test_lap_positions_rejects_too_many_laps():
    data = bytearray(
        make_lap_positions_packet()
    )

    # num_laps
    data[HEADER_SIZE] = MAX_NUM_LAPS_IN_LAP_POSITIONS_HISTORY_PACKET + 1

    with pytest.raises(ValueError,match="num_laps"):
        LapPositionsPacket.from_bytes(bytes(data))