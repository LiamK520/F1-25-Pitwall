import struct

import pytest

from tests.helpers import make_header

from udp.constants import NUM_CARS
from udp.header import HEADER_SIZE
from udp.packet_id import PacketId
from udp.car_setup import CAR_SETUP_STRUCT, CAR_SETUP_STRUCT_SIZE,CAR_SETUP_PACKET_SIZE, CarSetupPacket


def make_setup(
    front_wing: int = 25,
    rear_wing: int = 20,
    fuel_load: float = 30.5,
) -> bytes:

    return CAR_SETUP_STRUCT.pack(
        front_wing,        # front wing
        rear_wing,         # rear wing
        60,                # on throttle
        50,                # off throttle

        -3.5,              # front camber
        -2.0,              # rear camber
        0.10,              # front toe
        0.20,              # rear toe

        10,                # front suspension
        8,                 # rear suspension
        7,                 # front anti-roll bar
        6,                 # rear anti-roll bar
        25,                # front ride height
        30,                # rear ride height
        100,               # brake pressure
        55,                # brake bias
        40,                # engine braking

        22.5,              # rear left tyre pressure
        22.6,              # rear right tyre pressure
        24.1,              # front left tyre pressure
        24.2,              # front right tyre pressure

        5,                 # ballast
        fuel_load,
    )


def make_car_setup_packet(next_front_wing_value: float = 27.5) -> bytes:

    data = make_header(
        PacketId.CAR_SETUPS,
        player_car_index=0,
    )

    for car_idx in range(NUM_CARS):
        data += make_setup(
            front_wing=car_idx,
            rear_wing=car_idx + 1,
            fuel_load=20.0 + car_idx,
        )

    data += struct.pack("<f", next_front_wing_value)

    return data

# test

def test_car_setup_struct_size():
    assert CAR_SETUP_STRUCT_SIZE == 50


def test_car_setup_packet_size():
    data = make_car_setup_packet()

    assert len(data) == CAR_SETUP_PACKET_SIZE
    assert len(data) == 1133


def test_car_setup_decodes_setup():
    packet = CarSetupPacket.from_bytes(make_car_setup_packet())

    setup = packet.car_setup_data[0]

    assert setup.front_wing == 0
    assert setup.rear_wing == 1

    assert setup.on_throttle == 60
    assert setup.off_throttle == 50

    assert setup.front_camber == pytest.approx(-3.5)
    assert setup.rear_camber == pytest.approx(-2.0)
    assert setup.front_toe == pytest.approx(0.10)
    assert setup.rear_toe == pytest.approx(0.20)

    assert setup.front_suspension == 10
    assert setup.rear_suspension == 8

    assert setup.brake_pressure == 100
    assert setup.brake_bias == 55
    assert setup.engine_braking == 40

    assert setup.ballast == 5
    assert setup.fuel_load == pytest.approx(20.0)


def test_car_setup_decodes_multiple_cars():
    packet = CarSetupPacket.from_bytes(make_car_setup_packet())

    assert len(packet.car_setup_data) == NUM_CARS

    assert packet.car_setup_data[0].front_wing == 0
    assert packet.car_setup_data[5].front_wing == 5
    assert packet.car_setup_data[10].front_wing == 10


def test_car_setup_decodes_last_car():
    packet = CarSetupPacket.from_bytes(make_car_setup_packet())

    last = packet.car_setup_data[NUM_CARS - 1]

    assert last.front_wing == 21
    assert last.rear_wing == 22
    assert last.fuel_load == pytest.approx(41.0)


def test_car_setup_decodes_next_front_wing_value():
    packet = CarSetupPacket.from_bytes(make_car_setup_packet(next_front_wing_value=27.5))

    assert packet.next_front_wing_value == pytest.approx(27.5)


def test_car_setup_rejects_wrong_packet_size():
    data = make_car_setup_packet()

    with pytest.raises(ValueError):
        CarSetupPacket.from_bytes(data[:-1])