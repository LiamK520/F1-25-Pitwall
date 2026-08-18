import struct

import pytest

from tests.helpers import make_header

from udp.packet_id import PacketId
from udp.session_history import LAP_HISTORY_SIZE, LAP_HISTORY_STRUCT, MAX_LAPS_IN_HISTORY, MAX_TYRE_STINTS, SESSION_HISTORY_HEADER_STRUCT, SESSION_HISTORY_PACKET_SIZE, \
    TYRE_STINT_HISTORY_SIZE, TYRE_STINT_HISTORY_STRUCT, LapHistoryData, SessionHistoryPacket, TyreStintHistoryData


def make_lap_history(
    lap_time_in_ms: int = 90000,
    sector1_ms: int = 30000,
    sector1_minutes: int = 0,
    sector2_ms: int = 29500,
    sector2_minutes: int = 0,
    sector3_ms: int = 30500,
    sector3_minutes: int = 0,
    valid_flags: int = 0x0F,
) -> bytes:

    return struct.pack(
        "<IHBHBHBB",
        lap_time_in_ms,
        sector1_ms,
        sector1_minutes,
        sector2_ms,
        sector2_minutes,
        sector3_ms,
        sector3_minutes,
        valid_flags,
    )


def make_tyre_stint_history(
    end_lap: int = 10,
    actual_compound: int = 18,
    visual_compound: int = 17,
) -> bytes:

    return struct.pack(
        "<BBB",
        end_lap,
        actual_compound,
        visual_compound,
    )


def make_session_history_packet() -> bytes:

    data = make_header(
        PacketId.SESSION_HISTORY,
        player_car_index=4,
    )

    data += struct.pack(
        "<BBBBBBB",
        4,      # car idx
        3,      # num laps
        2,      # num tyre stints
        2,      # best lap
        1,      # best sector 1
        2,      # best sector 2
        3,      # best sector 3
    )

    laps = [
        make_lap_history(
            lap_time_in_ms=91000,
            valid_flags=0x0F,
        ),
        make_lap_history(
            lap_time_in_ms=89500,
            valid_flags=0x0F,
        ),
        make_lap_history(
            lap_time_in_ms=20000,
            valid_flags=0x00,
        ),
    ]

    for lap in laps:
        data += lap

    data += bytes(
        (MAX_LAPS_IN_HISTORY - len(laps))
        * LAP_HISTORY_SIZE
    )

    stints = [
        make_tyre_stint_history(
            end_lap=2,
            actual_compound=18,
            visual_compound=17,
        ),
        make_tyre_stint_history(
            end_lap=255,
            actual_compound=17,
            visual_compound=16,
        ),
    ]

    for stint in stints:
        data += stint

    data += bytes(
        (MAX_TYRE_STINTS - len(stints))
        * TYRE_STINT_HISTORY_SIZE
    )

    return data

def test_session_history_struct_sizes():
    assert LAP_HISTORY_STRUCT.size == 14
    assert TYRE_STINT_HISTORY_STRUCT.size == 3
    assert SESSION_HISTORY_HEADER_STRUCT.size == 7


def test_session_history_packet_size():
    data = make_session_history_packet()

    assert len(data) == SESSION_HISTORY_PACKET_SIZE


def test_lap_history_data_decodes():
    data = make_lap_history(
        lap_time_in_ms=91234,
        sector1_ms=30123,
        sector2_ms=29999,
        sector3_ms=31112,
        valid_flags=0x0F,
    )

    lap = LapHistoryData.from_bytes(
        data,
        0,
    )

    assert lap.lap_time_in_ms == 91234

    assert lap.sector1_time_ms_part == 30123
    assert lap.sector2_time_ms_part == 29999
    assert lap.sector3_time_ms_part == 31112

    assert lap.lap_valid_bit_flags == 0x0F


def test_tyre_stint_history_decodes():
    data = make_tyre_stint_history(
        end_lap=12,
        actual_compound=18,
        visual_compound=17,
    )

    stint = TyreStintHistoryData.from_bytes(
        data,
        0,
    )

    assert stint.end_lap == 12
    assert stint.tyre_actual_compound == 18
    assert stint.tyre_visual_compound == 17


def test_session_history_decodes_header_fields():
    packet = SessionHistoryPacket.from_bytes(
        make_session_history_packet()
    )

    assert packet.car_idx == 4

    assert packet.num_laps == 3
    assert packet.num_tyre_stints == 2

    assert packet.best_lap_time_lap_num == 2
    assert packet.best_sector1_lap_num == 1
    assert packet.best_sector2_lap_num == 2
    assert packet.best_sector3_lap_num == 3


def test_session_history_only_stores_valid_laps():
    packet = SessionHistoryPacket.from_bytes(
        make_session_history_packet()
    )

    assert len(packet.lap_history) == 3

    assert packet.lap_history[0].lap_time_in_ms == 91000
    assert packet.lap_history[1].lap_time_in_ms == 89500
    assert packet.lap_history[2].lap_time_in_ms == 20000


def test_session_history_decodes_tyre_stints():
    packet = SessionHistoryPacket.from_bytes(
        make_session_history_packet()
    )

    assert len(packet.tyre_stints) == 2

    first = packet.tyre_stints[0]
    second = packet.tyre_stints[1]

    assert first.end_lap == 2
    assert first.tyre_actual_compound == 18

    assert second.end_lap == 255
    assert second.tyre_actual_compound == 17


def test_session_history_uses_fixed_lap_array_offset():
    """
    make sure tyre stint is read after fixed 100 size array and not just after number of valid laps
    """

    packet = SessionHistoryPacket.from_bytes(
        make_session_history_packet()
    )

    assert packet.tyre_stints[0].end_lap == 2
    assert packet.tyre_stints[1].end_lap == 255


def test_session_history_rejects_wrong_packet_size():
    data = make_session_history_packet()

    with pytest.raises(ValueError):
        SessionHistoryPacket.from_bytes(
            data[:-1]
        )


def test_session_history_rejects_too_many_laps():
    data = bytearray(
        make_session_history_packet()
    )

    # header is 29 bytes:'
    # car_idx is byte 29
    # num_laps is byte 30
    data[30] = 101

    with pytest.raises(
        ValueError,
        match="Invalid number of laps",
    ):
        SessionHistoryPacket.from_bytes(
            bytes(data)
        )


def test_session_history_rejects_too_many_tyre_stints():
    data = bytearray(
        make_session_history_packet()
    )

    # num_tyre_stints is byte 31.
    data[31] = 9

    with pytest.raises(
        ValueError,
        match="Invalid number of tyre stints",
    ):
        SessionHistoryPacket.from_bytes(
            bytes(data)
        )