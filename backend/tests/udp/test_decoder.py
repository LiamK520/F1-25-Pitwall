import struct

import pytest

from tests.helpers import make_header
from udp.constants import NUM_CARS
from udp.decoder import decode_packet
from udp.motion import MotionPacket
from udp.packet_id import PacketId

CAR_MOTION_FORMAT = "<ffffffhhhhhhffffff"

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
    data = make_header(PacketId.MOTION_EX)

    packet = decode_packet(data)

    assert packet is None


def test_unknown_packet_id():
    data = make_header(99)

    with pytest.raises(ValueError):
        decode_packet(data)