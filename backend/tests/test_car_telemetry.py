import struct

import pytest

from tests.helpers import make_header
from udp.car_telemetry import CAR_TELEMETRY_PACKET_SIZE, CAR_TELEMETRY_SIZE, CarTelemetryData, CarTelemetryPacket
from udp.constants import NUM_CARS
from udp.packet_id import PacketId

# see udp definition for description
CAR_TELEMETRY_FORMAT = "<HfffBbHBBH4H4B4BH4f4B"

def make_car_telemetry(
    speed: int = 300,
    throttle: float = 0.75,
    gear: int = 7,
) -> bytes:
    return struct.pack(
        CAR_TELEMETRY_FORMAT,
        speed,

        throttle,
        -0.25,          # steer
        0.5,            # brake

        0,              # clutch
        gear,
        11000,          # engine RPM

        1,              # DRS
        80,             # rev lights percent
        0b111111,       # rev lights bit value

        # brake temps
        600,
        610,
        590,
        595,

        # tyre temps surface
        95,
        96,
        92,
        93,

        # tyre temsp core
        90,
        91,
        88,
        89,

        105,            # engine temp

        # Tyre pressures
        23.5,
        23.6,
        21.5,
        21.6,

        # surface types
        0,
        0,
        0,
        0,
    )

def make_car_telemetry_packet() -> bytes:
    data = make_header(PacketId.CAR_TELEMETRY)

    for i in range(NUM_CARS):
        data += make_car_telemetry(
            speed=280 + i,
            throttle=0.75,
            gear=7,
        )

    # mfds and sug gear
    data += struct.pack("<BBb", 255, 255, 6)

    return data

def test_car_telemetry_size():
    assert CAR_TELEMETRY_SIZE == 60


def test_car_telemetry_packet_size():
    assert CAR_TELEMETRY_PACKET_SIZE == 1352


def test_car_telemetry_reads():
    data = make_car_telemetry(
        speed=315,
        throttle=0.75,
        gear=8,
    )

    telemetry = CarTelemetryData.from_bytes(data, 0)

    assert telemetry.speed == 315
    assert telemetry.throttle == 0.75
    assert telemetry.steer == -0.25
    assert telemetry.brake == 0.5

    assert telemetry.clutch == 0
    assert telemetry.gear == 8
    assert telemetry.engine_rpm == 11000

    assert telemetry.drs == 1
    assert telemetry.rev_lights_percent == 80

    assert telemetry.brakes_temperature == (
        600,
        610,
        590,
        595,
    )

    assert telemetry.tyres_surface_temperature == (
        95,
        96,
        92,
        93,
    )

    assert telemetry.tyres_inner_temperature == (
        90,
        91,
        88,
        89,
    )

    assert telemetry.engine_temperature == 105

    assert telemetry.tyres_pressure == pytest.approx(
        (
            23.5,
            23.6,
            21.5,
            21.6,
        )
    )

    assert telemetry.surface_type == (0, 0, 0, 0)

def test_car_telemetry_packet_reads_all_cars():
    data = make_car_telemetry_packet()

    packet = CarTelemetryPacket.from_bytes(data)

    assert packet.header.packet_id == PacketId.CAR_TELEMETRY
    assert len(packet.cars) == NUM_CARS

    assert packet.cars[0].speed == 280
    assert packet.cars[5].speed == 285
    assert packet.cars[21].speed == 301

    assert packet.mfd_panel_index == 255
    assert packet.mfd_panel_index_secondary_player == 255
    assert packet.suggested_gear == 6


def test_car_telemetry_packet_rejects_wrong_size():
    data = bytes(100)

    with pytest.raises(ValueError):
        CarTelemetryPacket.from_bytes(data)