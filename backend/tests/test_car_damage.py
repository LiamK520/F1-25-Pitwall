import struct

import pytest

from tests.helpers import make_header
from udp.car_damage import CAR_DAMAGE_PACKET_SIZE, CAR_DAMAGE_SIZE, CarDamageData, CarDamagePacket
from udp.constants import NUM_CARS
from udp.packet_id import PacketId


CAR_DAMAGE_FORMAT = "<4f4B4B4B18B"

# create funcs

def make_car_damage(
    tyre_wear: float = 10.0,
    front_left_wing_damage: int = 0,
    engine_damage: int = 0,
) -> bytes:
    return struct.pack(
        CAR_DAMAGE_FORMAT,

        # Tyre wear
        tyre_wear,
        tyre_wear + 1,
        tyre_wear + 2,
        tyre_wear + 3,

        # Tyre damage
        1,
        2,
        3,
        4,

        # Brake damage
        5,
        6,
        7,
        8,

        # Tyre blisters
        9,
        10,
        11,
        12,

        # Aero damage
        front_left_wing_damage,
        20,     # front right wing
        5,      # rear wing
        6,      # floor
        7,      # diffuser
        8,      # sidepod

        # Faults
        0,      # DRS fault
        0,      # ERS fault

        # General damage
        15,             # gearbox
        engine_damage,  # engine

        # Engine component wear
        21,     # MGU-H
        22,     # ES
        23,     # CE
        24,     # ICE
        25,     # MGU-K
        26,     # TC

        # Terminal engine faults
        0,      # engine blown
        0,      # engine seized
    )


def make_car_damage_packet() -> bytes:
    data = make_header(PacketId.CAR_DAMAGE)

    for i in range(NUM_CARS):
        data += make_car_damage(
            tyre_wear=10.0 + i,
            front_left_wing_damage=i,
            engine_damage=i,
        )

    return data

# actual tests

def test_car_damage_size():
    assert CAR_DAMAGE_SIZE == 46


def test_car_damage_packet_size():
    assert CAR_DAMAGE_PACKET_SIZE == 1041

def test_car_damage_reads():
    data = make_car_damage(
        tyre_wear=12.5,
        front_left_wing_damage=35,
        engine_damage=14,
    )

    damage = CarDamageData.from_bytes(data, 0)

    assert damage.tyres_wear == pytest.approx(
        (12.5, 13.5, 14.5, 15.5)
    )

    assert damage.tyres_damage == (1, 2, 3, 4)
    assert damage.brakes_damage == (5, 6, 7, 8)
    assert damage.tyre_blisters == (9, 10, 11, 12)

    assert damage.front_left_wing_damage == 35
    assert damage.front_right_wing_damage == 20
    assert damage.rear_wing_damage == 5

    assert damage.drs_fault == 0
    assert damage.ers_fault == 0

    assert damage.gearbox_damage == 15
    assert damage.engine_damage == 14

    assert damage.engine_mguh_wear == 21
    assert damage.engine_es_wear == 22
    assert damage.engine_ce_wear == 23
    assert damage.engine_ice_wear == 24
    assert damage.engine_mguk_wear == 25
    assert damage.engine_tc_wear == 26

    assert damage.engine_blown == 0
    assert damage.engine_seized == 0


def test_car_damage_packet_reads_all_cars():
    data = make_car_damage_packet()

    packet = CarDamagePacket.from_bytes(data)

    assert packet.header.packet_id == PacketId.CAR_DAMAGE
    assert len(packet.cars) == NUM_CARS

    assert packet.cars[0].tyres_wear[0] == pytest.approx(10.0)
    assert packet.cars[0].front_left_wing_damage == 0

    assert packet.cars[5].tyres_wear[0] == pytest.approx(15.0)
    assert packet.cars[5].front_left_wing_damage == 5
    assert packet.cars[5].engine_damage == 5

    assert packet.cars[21].tyres_wear[0] == pytest.approx(31.0)
    assert packet.cars[21].front_left_wing_damage == 21


def test_car_damage_packet_rejects_wrong_size():
    with pytest.raises(ValueError):
        CarDamagePacket.from_bytes(bytes(100))