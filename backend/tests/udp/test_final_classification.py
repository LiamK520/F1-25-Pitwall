import struct

import pytest

from tests.helpers import make_header

from udp.constants import NUM_CARS
from udp.final_classification import FINAL_CLASSIFICATION_PACKET_SIZE, FINAL_CLASSIFICATION_SIZE, FINAL_CLASSIFICATION_STRUCT, MAX_TYRE_STINTS, FinalClassificationData, FinalClassificationPacket
from udp.packet_id import PacketId


def make_final_classification(
    position: int = 1,
    num_laps: int = 10,
    grid_position: int = 3,
    points: int = 25,
    num_pit_stops: int = 1,
    result_status: int = 3,
    result_reason: int = 2,
    best_lap_time_in_ms: int = 91234,
    total_race_time: float = 1234.567,
    penalties_time: int = 5,
    num_penalties: int = 1,
    tyre_stints_actual: tuple[int, ...] = (17, 18),
    tyre_stints_visual: tuple[int, ...] = (16, 17),
    tyre_stints_end_laps: tuple[int, ...] = (5, 10),
) -> bytes:
    """make final classification data binary"""

    num_tyre_stints = len(tyre_stints_actual)

    assert len(tyre_stints_visual) == num_tyre_stints
    assert len(tyre_stints_end_laps) == num_tyre_stints
    assert num_tyre_stints <= MAX_TYRE_STINTS

    actual = (
        list(tyre_stints_actual)
        + [0] * (MAX_TYRE_STINTS - num_tyre_stints)
    )

    visual = (
        list(tyre_stints_visual)
        + [0] * (MAX_TYRE_STINTS - num_tyre_stints)
    )

    end_laps = (
        list(tyre_stints_end_laps)
        + [0] * (MAX_TYRE_STINTS - num_tyre_stints)
    )

    return FINAL_CLASSIFICATION_STRUCT.pack(
        position,
        num_laps,
        grid_position,
        points,
        num_pit_stops,
        result_status,
        result_reason,
        best_lap_time_in_ms,
        total_race_time,
        penalties_time,
        num_penalties,
        num_tyre_stints,
        *actual,
        *visual,
        *end_laps,
    )


def make_final_classification_packet(
    num_cars: int = 3,
) -> bytes:
    """Build a complete synthetic Final Classification packet."""

    data = make_header(
        PacketId.FINAL_CLASSIFICATION,
        player_car_index=0,
    )

    data += struct.pack(
        "<B",
        num_cars,
    )

    for i in range(NUM_CARS):
        data += make_final_classification(
            position=i + 1,
            grid_position=NUM_CARS - i,
            best_lap_time_in_ms=90000 + i,
        )

    return data


def test_final_classification_struct_size():
    assert FINAL_CLASSIFICATION_STRUCT.size == 46

    assert (
        FINAL_CLASSIFICATION_STRUCT.size
        == FINAL_CLASSIFICATION_SIZE
    )


def test_final_classification_packet_size():
    data = make_final_classification_packet()

    assert len(data) == FINAL_CLASSIFICATION_PACKET_SIZE


def test_final_classification_data_decodes():
    data = make_final_classification(
        position=2,
        num_laps=15,
        grid_position=6,
        points=18,
        num_pit_stops=2,
        result_status=3,
        result_reason=2,
        best_lap_time_in_ms=88765,
        total_race_time=1543.21,
        penalties_time=10,
        num_penalties=2,
    )

    result = FinalClassificationData.from_bytes(
        data,
        0,
    )

    assert result.position == 2
    assert result.num_laps == 15
    assert result.grid_position == 6

    assert result.points == 18
    assert result.num_pit_stops == 2

    assert result.result_status == 3
    assert result.result_reason == 2

    assert result.best_lap_time_in_ms == 88765

    assert result.total_race_time == pytest.approx(
        1543.21
    )

    assert result.penalties_time == 10
    assert result.num_penalties == 2


def test_final_classification_decodes_tyre_stints():
    data = make_final_classification(
        tyre_stints_actual=(17, 18, 19),
        tyre_stints_visual=(16, 17, 17),
        tyre_stints_end_laps=(5, 11, 18),
    )

    result = FinalClassificationData.from_bytes(
        data,
        0,
    )

    assert result.num_tyre_stints == 3

    assert result.tyre_stints_actual == (
        17,
        18,
        19,
    )

    assert result.tyre_stints_visual == (
        16,
        17,
        17,
    )

    assert result.tyre_stints_end_laps == (
        5,
        11,
        18,
    )


def test_final_classification_packet_decodes_num_cars():
    packet = FinalClassificationPacket.from_bytes(
        make_final_classification_packet(
            num_cars=3,
        )
    )

    assert packet.num_cars == 3
    assert len(packet.classifications) == 3


def test_final_classification_decodes_multiple_cars():
    packet = FinalClassificationPacket.from_bytes(
        make_final_classification_packet(
            num_cars=3,
        )
    )

    assert packet.classifications[0].position == 1
    assert packet.classifications[1].position == 2
    assert packet.classifications[2].position == 3

    assert (
        packet.classifications[0].best_lap_time_in_ms
        == 90000
    )

    assert (
        packet.classifications[2].best_lap_time_in_ms
        == 90002
    )


def test_final_classification_rejects_wrong_packet_size():
    data = make_final_classification_packet()

    with pytest.raises(ValueError):
        FinalClassificationPacket.from_bytes(
            data[:-1]
        )


def test_final_classification_rejects_too_many_cars():
    data = bytearray(
        make_final_classification_packet()
    )

    data[29] = NUM_CARS + 1

    with pytest.raises(
        ValueError,
        match="Invalid number of cars",
    ):
        FinalClassificationPacket.from_bytes(
            bytes(data)
        )


def test_final_classification_rejects_too_many_tyre_stints():
    data = bytearray(
        make_final_classification()
    )

    # Offset within FinalClassificationData:
    #
    # 7 uint8             = 7
    # uint32              = 4
    # double              = 8
    # penalties_time      = 1
    # num_penalties       = 1
    #
    # num_tyre_stints is therefore byte 21.
    data[21] = MAX_TYRE_STINTS + 1

    with pytest.raises(
        ValueError,
        match="Invalid number of tyre stints",
    ):
        FinalClassificationData.from_bytes(
            bytes(data),
            0,
        )