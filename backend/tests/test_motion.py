import struct

from udp.motion import CAR_MOTION_SIZE, MOTION_PACKET_SIZE, NUM_CARS, MotionPacket

HEADER_FORMAT = "<HBBBBBQfIIBB"
CAR_FORMAT = "<ffffffhhhhhhffffff"

def make_header(packet_id: int) -> bytes:
    # see test header for field description
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


def make_car_motion(index: int) -> bytes:
    return struct.pack(
        CAR_FORMAT,
        100.0 + index,  # position x
        20.0,           # position y
        200.0 + index,  # position z

        10.0,           # velocity x
        0.0,            # velocity y
        20.0,           # velocity z

        100,             # forward x
        0,               # forward y
        200,             # forward z

        200,             # right x
        0,               # right y
        100,             # right z

        1.5,             # lateral G
        2.5,             # longitudinal G
        0.1,             # vertical G

        0.5,             # yaw
        0.1,             # pitch
        0.05,            # roll
    )

def test_car_motion_size():
    assert CAR_MOTION_SIZE == 60


def test_motion_packet_size():
    assert MOTION_PACKET_SIZE == 1349


def test_motion_packet_all_cars():
    data = make_header(0)

    for i in range(NUM_CARS):
        data += make_car_motion(i)

    packet = MotionPacket.from_bytes(data)

    # assert a snippet of cars

    assert packet.cars[0].world_position_x == 100.0
    assert packet.cars[0].world_position_z == 200.0

    assert packet.cars[5].world_position_x == 105.0
    assert packet.cars[5].world_position_z == 205.0

    assert packet.cars[21].world_position_x == 121.0
    assert packet.cars[21].world_position_z == 221.0

def test_motion_packet_rejects_wrong_size():
    data = bytes(100)

    try:
        MotionPacket.from_bytes(data)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "Expected ValueError for invalid Motion packet size"
        )
