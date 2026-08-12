import struct

import pytest

from tests.helpers import make_header
from udp.event import EVENT_DETAILS_SIZE, EVENT_PACKET_SIZE, CollisionEvent, EventPacket, FastestLapEvent, PenaltyEvent, SafetyCarEvent, SpeedTrapEvent
from udp.packet_id import PacketId

# TODO: Add tests for every event type. Right now only a handful are covered.


def make_event_packet(
    event_code: str,
    details: bytes = b"",
) -> bytes:
    data = make_header(PacketId.EVENT)

    data += event_code.encode("ascii")

    if len(details) > EVENT_DETAILS_SIZE:
        raise ValueError("Event details too large")

    data += details

    # Event union always occupies 12 bytes
    data += bytes(
        EVENT_DETAILS_SIZE - len(details)
    )

    return data


def test_event_packet_size():
    data = make_event_packet("SSTA")

    assert EVENT_PACKET_SIZE == 45
    assert len(data) == EVENT_PACKET_SIZE


def test_event_without_details():
    data = make_event_packet("SSTA")

    packet = EventPacket.from_bytes(data)

    assert packet.header.packet_id == PacketId.EVENT
    assert packet.event_code == "SSTA"
    assert packet.details is None


def test_fastest_lap_event():
    data = make_event_packet("FTLP", struct.pack("<Bf",7,82.456,))

    packet = EventPacket.from_bytes(data)

    assert packet.event_code == "FTLP"
    assert isinstance(packet.details,FastestLapEvent)

    assert packet.details.vehicle_idx == 7
    assert packet.details.lap_time == pytest.approx(
        82.456
    )


def test_penalty_event():
    data = make_event_packet(
        "PENA",
        struct.pack(
            "<7B",
            2,      # penalty type
            5,      # infringement type
            10,     # vehicle
            7,      # other vehicle
            5,      # seconds
            12,     # lap
            1,      # places gained
        ),
    )

    packet = EventPacket.from_bytes(data)

    assert isinstance(packet.details,PenaltyEvent)

    assert packet.details.penalty_type == 2
    assert packet.details.infringement_type == 5
    assert packet.details.vehicle_idx == 10
    assert packet.details.other_vehicle_idx == 7
    assert packet.details.time == 5
    assert packet.details.lap_num == 12
    assert packet.details.places_gained == 1


def test_speed_trap_event():
    data = make_event_packet(
        "SPTP",
        struct.pack(
            "<BfBBBf",
            4,          # vehicle
            335.5,      # speed
            1,          # overall fastest
            1,          # driver's fastest
            4,          # fastest vehicle
            335.5,      # fastest session speed
        ),
    )

    packet = EventPacket.from_bytes(data)

    assert isinstance(packet.details,SpeedTrapEvent)

    assert packet.details.vehicle_idx == 4
    assert packet.details.speed == pytest.approx(335.5)
    assert packet.details.is_overall_fastest_in_session == 1
    assert packet.details.fastest_vehicle_idx_in_session == 4
    assert packet.details.fastest_speed_in_session == pytest.approx(335.5)


def test_safety_car_event():
    data = make_event_packet(
        "SCAR",
        struct.pack(
            "<BB",
            1,      # full safety car
            0,      # deployed
        ),
    )

    packet = EventPacket.from_bytes(data)

    assert isinstance(packet.details,SafetyCarEvent)

    assert packet.details.safety_car_type == 1
    assert packet.details.event_type == 0


def test_collision_event():
    data = make_event_packet(
        "COLL",
        struct.pack(
            "<BB",
            8,
            12,
        ),
    )

    packet = EventPacket.from_bytes(data)

    assert isinstance(packet.details,CollisionEvent)

    assert packet.details.vehicle1_idx == 8
    assert packet.details.vehicle2_idx == 12


def test_event_rejects_unknown_code():
    data = make_event_packet("XXXX")

    with pytest.raises(ValueError):
        EventPacket.from_bytes(data)


def test_event_rejects_wrong_size():
    with pytest.raises(ValueError):
        EventPacket.from_bytes(bytes(20))