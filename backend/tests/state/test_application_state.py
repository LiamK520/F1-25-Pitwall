import pytest

from state.application_state import ApplicationState, CarState

from tests.helpers import make_header
from tests.udp.test_car_damage import make_car_damage
from tests.udp.test_event import make_event_packet
from tests.udp.test_session import make_session_packet

from udp.car_damage import CarDamagePacket
from udp.constants import NUM_CARS
from udp.event import EVENT_DETAILS_SIZE, EventPacket
from udp.packet_id import PacketId
from udp.session import SessionPacket


def make_damage_packet(
    session_uid: int = 123456789,
    player_car_index: int = 0,
) -> CarDamagePacket:
    """
    Build a CarDamagePacket with distinct damage values for every car.
    """

    data = make_header(
        PacketId.CAR_DAMAGE,
        player_car_index=player_car_index,
        session_uid=session_uid,
    )

    for i in range(NUM_CARS):
        data += make_car_damage(
            tyre_wear=10.0 + i,
            front_left_wing_damage=i,
            engine_damage=i,
        )

    return CarDamagePacket.from_bytes(data)


def make_session_event(
    session_uid: int,
    player_car_index: int = 0,
) -> EventPacket:
    """in
    Make session event for specific session"""

    data = make_header(
        PacketId.EVENT,
        session_uid=session_uid,
        player_car_index=player_car_index,
    )

    data += b"SSTA"
    data += bytes(EVENT_DETAILS_SIZE)

    return EventPacket.from_bytes(data)


def test_application_state_initialises_car_slots():
    state = ApplicationState()

    assert len(state.cars) == NUM_CARS

    for i, car in enumerate(state.cars):
        assert isinstance(car, CarState)
        assert car.index == i

        assert car.participant is None
        assert car.motion is None
        assert car.lap is None
        assert car.telemetry is None
        assert car.status is None
        assert car.damage is None


def test_damage_packet_updates_correct_cars():
    state = ApplicationState()

    packet = make_damage_packet()

    state.update(packet)

    assert state.cars[0].damage is not None
    assert state.cars[5].damage is not None
    assert state.cars[21].damage is not None

    assert state.cars[0].damage.engine_damage == 0
    assert state.cars[5].damage.engine_damage == 5
    assert state.cars[21].damage.engine_damage == 21

    assert (
        state.cars[5].damage.front_left_wing_damage
        == 5
    )

    assert state.cars[21].damage.tyres_wear[0] == pytest.approx(
        31.0
    )


def test_player_car_resolves_from_header():
    state = ApplicationState()

    packet = make_damage_packet(
        player_car_index=7,
    )

    state.update(packet)

    assert state.player_car_index == 7

    assert state.player_car is state.cars[7]
    assert state.player_car.index == 7

    assert state.player_car.damage is not None
    assert state.player_car.damage.engine_damage == 7


def test_invalid_secondary_player_becomes_none():
    state = ApplicationState()

    # make_header currently uses 255 for the secondary player,
    # representing no secondary player.
    packet = make_damage_packet()

    state.update(packet)

    assert state.secondary_player_car_index is None


def test_session_packet_updates_session_state():
    state = ApplicationState()

    packet = SessionPacket.from_bytes(
        make_session_packet()
    )

    state.update(packet)

    assert state.session is packet

    assert state.session_uid == packet.header.session_uid

    assert state.session.session_type == 15
    assert state.session.track_id == 7
    assert state.session.track_length == 5891


def test_event_packet_is_added_to_event_history():
    state = ApplicationState()

    packet = EventPacket.from_bytes(
        make_event_packet("SSTA")
    )

    state.update(packet)

    assert len(state.events) == 1

    assert state.events[0] is packet
    assert state.events[0].event_code == "SSTA"


def test_multiple_events_are_preserved_in_order():
    state = ApplicationState()

    session_started = EventPacket.from_bytes(
        make_event_packet("SSTA")
    )

    lights_out = EventPacket.from_bytes(
        make_event_packet("LGOT")
    )

    state.update(session_started)
    state.update(lights_out)

    assert len(state.events) == 2

    assert state.events[0].event_code == "SSTA"
    assert state.events[1].event_code == "LGOT"


def test_new_session_uid_resets_previous_state():
    old_session_uid = 111
    new_session_uid = 222

    state = ApplicationState()

    # Add state belonging to the old session.
    old_damage = make_damage_packet(
        session_uid=old_session_uid,
        player_car_index=4,
    )

    old_event = make_session_event(
        session_uid=old_session_uid,
        player_car_index=4,
    )

    state.update(old_damage)
    state.update(old_event)

    assert state.session_uid == old_session_uid
    assert state.player_car_index == 4
    assert len(state.events) == 1

    old_damage_object = state.cars[4].damage

    assert old_damage_object is not None

    # A packet from a different session should reset everything
    # before its own data is applied.
    new_damage = make_damage_packet(
        session_uid=new_session_uid,
        player_car_index=8,
    )

    state.update(new_damage)

    assert state.session_uid == new_session_uid
    assert state.player_car_index == 8

    # old events gone
    assert state.events == []

    # session state from previous should be gone
    assert state.session is None

    # new session recreates cars, so this should not be same object
    assert state.cars[4].damage is not old_damage_object

    # ensure new packet applied
    assert state.cars[8].damage is not None
    assert state.cars[8].damage.engine_damage == 8


def test_reset_clears_application_state():
    state = ApplicationState()

    damage_packet = make_damage_packet(
        player_car_index=7,
    )

    event_packet = make_session_event(
        session_uid=damage_packet.header.session_uid,
        player_car_index=7,
    )

    state.update(damage_packet)
    state.update(event_packet)

    assert state.player_car_index == 7
    assert state.cars[7].damage is not None
    assert len(state.events) == 1

    state.reset()

    # check everythin gone

    assert state.session_uid is None
    assert state.session is None

    assert state.player_car_index is None
    assert state.secondary_player_car_index is None

    assert state.num_active_cars == 0
    assert state.events == []

    assert len(state.cars) == NUM_CARS

    for car in state.cars:
        assert car.participant is None
        assert car.motion is None
        assert car.lap is None
        assert car.telemetry is None
        assert car.status is None
        assert car.damage is None