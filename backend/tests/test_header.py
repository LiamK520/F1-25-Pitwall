import struct

from udp.header import HEADER_SIZE, HEADER_STRUCT, PacketHeader

def test_header_size():
    assert HEADER_SIZE == 29
    assert HEADER_STRUCT.size == 29


def test_header_from_bytes():
    data = struct.pack(
        "<HBBBBBQfIIBB",
        2025,       # packet_format
        25,         # game_year
        1,          # game_major_version
        2,          # game_minor_version
        3,          # packet_version
        6,          # packet_id - Car Telemetry
        123456789,  # session_uid
        42.5,       # session_time
        100,        # frame_identifier
        105,        # overall_frame_identifier
        7,          # player_car_index
        255,        # secondary_player_car_index
    )

    header = PacketHeader.from_bytes(data)

    assert header.packet_format == 2025
    assert header.game_year == 25
    assert header.game_major_version == 1
    assert header.game_minor_version == 2
    assert header.packet_version == 3
    assert header.packet_id == 6
    assert header.session_uid == 123456789
    assert header.session_time == 42.5
    assert header.frame_identifier == 100
    assert header.overall_frame_identifier == 105
    assert header.player_car_index == 7
    assert header.secondary_player_car_index == 255

def test_header_rejects_short_data():
    data = bytes(28)

    try:
        PacketHeader.from_bytes(data)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for packet shorter than 29 bytes"
        )