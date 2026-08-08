import struct

from udp.packet_id import PacketId


HEADER_FORMAT = "<HBBBBBQfIIBB"


def make_header(
    packet_id: int | PacketId,
    player_car_index: int = 0,
    session_uid: int = 123456789,
    session_time: float = 42.5,
    frame_identifier: int = 100,
) -> bytes:
    return struct.pack(
        HEADER_FORMAT,
        2025,               # packet_format
        25,                 # game_year
        1,                  # game_major_version
        0,                  # game_minor_version
        1,                  # packet_version
        packet_id,
        session_uid,
        session_time,
        frame_identifier,
        frame_identifier,   # overall_frame_identifier
        player_car_index,
        255,                # secondary_player_car_index
    )