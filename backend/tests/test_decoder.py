import struct

import pytest

from udp.decoder import PacketId, decode_packet
from udp.motion import MotionPacket, NUM_CARS


HEADER_FORMAT = "<HBBBBBQfIIBB"
CAR_MOTION_FORMAT = "<ffffffhhhhhhffffff"

# TODO: rewriting these a lot now. Maybe centralise the creation functions?


def make_header(packet_id: int) -> bytes:
    return struct.pack(
        HEADER_FORMAT,
        2025,
        25,
        1,
        0,
        1,
        packet_id,
        123456789,
        42.5,
        100,
        100,
        0,
        255,
    )


def make_car_motion() -> bytes:
    return struct.pack(
        CAR_MOTION_FORMAT,
        100.0,
        20.0,
        200.0,
        10.0,
        0.0,
        20.0,
        100,
        0,
        200,
        200,
        0,
        100,
        1.5,
        2.5,
        0.1,
        0.5,
        0.1,
        0.05,
    )


def make_motion_packet() -> bytes:
    data = make_header(PacketId.MOTION)

    for _ in range(NUM_CARS):
        data += make_car_motion()

    return data


def test_decode_motion_packet():
    data = make_motion_packet()

    packet = decode_packet(data)

    assert isinstance(packet, MotionPacket)
    assert packet.header.packet_id == PacketId.MOTION
    assert len(packet.cars) == 22


def test_known_but_unimplemented_packet():
    # TODO: This will obviously need to be deleted later
    data = make_header(PacketId.CAR_TELEMETRY)

    with pytest.raises(NotImplementedError):
        decode_packet(data)


def test_unknown_packet_id():
    data = make_header(99)

    with pytest.raises(ValueError):
        decode_packet(data)