import struct

import pytest

from tests.helpers import make_header
from udp.car_status import CAR_STATUS_PACKET_SIZE, CAR_STATUS_SIZE, CarStatusData, CarStatusPacket
from udp.constants import NUM_CARS
from udp.packet_id import PacketId

CAR_STATUS_FORMAT = "<5B3f2H2BH3Bb3fB3fB"


def make_car_status(
    fuel_in_tank: float = 50.0,
    fuel_remaining_laps: float = 20.5,
    tyres_age_laps: int = 5,
) -> bytes:
    return struct.pack(
        CAR_STATUS_FORMAT,
        0,              # traction control
        0,              # ABS
        1,              # fuel mix - standard
        55,             # front brake bias
        0,              # pit limiter

        fuel_in_tank,
        110.0,          # fuel capacity
        fuel_remaining_laps,

        15000,          # max RPM
        4000,           # idle RPM

        8,              # max gears
        1,              # DRS allowed
        250,            # DRS activation distance

        18,             # actual compound - C3
        17,             # visual compound - medium
        tyres_age_laps,

        0,              # FIA flag - none

        550000.0,       # ICE power
        120000.0,       # MGU-K power
        3000000.0,      # ERS store energy

        2,              # ERS deploy mode - hotlap

        500000.0,       # harvested this lap MGU-K
        100000.0,       # harvested this lap MGU-H
        750000.0,       # deployed this lap

        0,              # network paused
    )

def make_car_status_packet() -> bytes:
    data = make_header(PacketId.CAR_STATUS)

    for i in range(NUM_CARS):
        data += make_car_status(
            fuel_in_tank=50.0 - i,
            fuel_remaining_laps=20.5 - i * 0.5,
            tyres_age_laps=i,
        )

    return data

def test_car_status_size():
    assert CAR_STATUS_SIZE == 55


def test_car_status_packet_size():
    assert CAR_STATUS_PACKET_SIZE == 1239

def test_car_status_reads():
    data = make_car_status(
        fuel_in_tank=42.5,
        fuel_remaining_laps=15.25,
        tyres_age_laps=7,
    )

    status = CarStatusData.from_bytes(data, 0)

    assert status.traction_control == 0
    assert status.anti_lock_brakes == 0
    assert status.front_brake_bias == 55

    assert status.fuel_in_tank == pytest.approx(42.5)
    assert status.fuel_capacity == pytest.approx(110.0)
    assert status.fuel_remaining_laps == pytest.approx(15.25)

    assert status.max_rpm == 15000
    assert status.max_gears == 8

    assert status.drs_allowed == 1
    assert status.drs_activation_distance == 250

    assert status.actual_tyre_compound == 18
    assert status.visual_tyre_compound == 17
    assert status.tyres_age_laps == 7

    assert status.vehicle_fia_flags == 0

    assert status.ers_store_energy == pytest.approx(3000000.0)
    assert status.ers_deploy_mode == 2
    assert status.ers_deployed_this_lap == pytest.approx(750000.0)

def test_car_status_packet_reads_all_cars():
    data = make_car_status_packet()

    packet = CarStatusPacket.from_bytes(data)

    assert packet.header.packet_id == PacketId.CAR_STATUS
    assert len(packet.cars) == NUM_CARS

    assert packet.cars[0].fuel_in_tank == pytest.approx(50.0)
    assert packet.cars[0].tyres_age_laps == 0

    assert packet.cars[5].fuel_in_tank == pytest.approx(45.0)
    assert packet.cars[5].tyres_age_laps == 5

    assert packet.cars[21].fuel_in_tank == pytest.approx(29.0)
    assert packet.cars[21].tyres_age_laps == 21


def test_car_status_packet_rejects_wrong_size():
    data = bytes(100)

    with pytest.raises(ValueError):
        CarStatusPacket.from_bytes(data)