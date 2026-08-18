import struct

import pytest

from tests.helpers import make_header

from udp.packet_id import PacketId
from udp.tyre_sets import NUM_TYRE_SETS, TYRE_SET_SIZE, TYRE_SET_STRUCT, TYRE_SETS_PACKET_SIZE, TyreSetData, TyreSetsPacket

def make_tyre_set(
    actual_compound: int = 18,
    visual_compound: int = 17,
    wear: int = 10,
    available: int = 1,
    recommended_session: int = 15,
    life_span: int = 20,
    usable_life: int = 25,
    lap_delta_time: int = -250,
    fitted: int = 0,
) -> bytes:

    return struct.pack(
        "<7BhB",
        actual_compound,
        visual_compound,
        wear,
        available,
        recommended_session,
        life_span,
        usable_life,
        lap_delta_time,
        fitted,
    )


def make_tyre_sets_packet() -> bytes:

    data = make_header(
        PacketId.TYRE_SETS,
        player_car_index=4,
    )

    data += struct.pack(
        "<B",
        4,
    )

    for i in range(NUM_TYRE_SETS):
        data += make_tyre_set(
            actual_compound=18,
            visual_compound=17,
            wear=i,
            available=1,
            recommended_session=15,
            life_span=20,
            usable_life=25,
            lap_delta_time=-250 + i,
            fitted=int(i == 3),
        )

    data += struct.pack("<B",3)

    return data


def test_tyre_set_struct_size():
    assert TYRE_SET_STRUCT.size == TYRE_SET_SIZE
    assert TYRE_SET_SIZE == 10


def test_tyre_sets_packet_size():
    data = make_tyre_sets_packet()

    assert len(data) == TYRE_SETS_PACKET_SIZE


def test_tyre_set_data_decodes():
    data = make_tyre_set(
        actual_compound=18,
        visual_compound=17,
        wear=12,
        available=1,
        recommended_session=15,
        life_span=18,
        usable_life=24,
        lap_delta_time=-321,
        fitted=1,
    )

    tyre_set = TyreSetData.from_bytes(
        data,
        0,
    )

    assert tyre_set.actual_tyre_compound == 18
    assert tyre_set.visual_tyre_compound == 17

    assert tyre_set.wear == 12
    assert tyre_set.available == 1

    assert tyre_set.recommended_session == 15

    assert tyre_set.life_span == 18
    assert tyre_set.usable_life == 24

    assert tyre_set.lap_delta_time == -321

    assert tyre_set.fitted == 1


def test_tyre_sets_packet_decodes_car_index():
    packet = TyreSetsPacket.from_bytes(
        make_tyre_sets_packet()
    )

    assert packet.car_idx == 4


def test_tyre_sets_packet_decodes_all_sets():
    packet = TyreSetsPacket.from_bytes(
        make_tyre_sets_packet()
    )

    assert len(packet.tyre_sets) == NUM_TYRE_SETS

    assert packet.tyre_sets[0].wear == 0
    assert packet.tyre_sets[10].wear == 10
    assert packet.tyre_sets[19].wear == 19

    assert packet.tyre_sets[0].lap_delta_time == -250
    assert packet.tyre_sets[19].lap_delta_time == -231


def test_tyre_sets_packet_decodes_fitted_set():
    packet = TyreSetsPacket.from_bytes(
        make_tyre_sets_packet()
    )

    assert packet.fitted_idx == 3

    assert packet.tyre_sets[
        packet.fitted_idx
    ].fitted == 1


def test_tyre_sets_packet_rejects_wrong_size():
    data = make_tyre_sets_packet()

    with pytest.raises(ValueError):
        TyreSetsPacket.from_bytes(
            data[:-1]
        )