import pytest

from state.application_state import ApplicationState, CarState

from tests.helpers import make_header
from tests.udp.test_car_damage import make_car_damage
from tests.udp.test_event import make_event_packet
from tests.udp.test_session import make_session_packet
from tests.udp.test_car_setups import make_car_setup_packet
from tests.udp.test_session_history import make_session_history_packet
from tests.udp.test_tyre_sets import make_tyre_sets_packet
from tests.udp.test_lap_positions import make_lap_positions_packet
from tests.udp.test_final_classification import make_final_classification_packet

from udp.car_damage import CarDamagePacket
from udp.constants import NUM_CARS
from udp.event import EVENT_DETAILS_SIZE, EventPacket
from udp.packet_id import PacketId
from udp.session import SessionPacket
from udp.car_setup import CarSetupPacket
from udp.session_history import SessionHistoryPacket
from udp.tyre_sets import TyreSetsPacket
from udp.lap_positions import LapPositionsPacket
from udp.final_classification import FinalClassificationPacket


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
        assert car.setup is None
        assert car.session_history is None
        assert car.tyre_sets is None

    assert state.lap_positions == {}
    assert state.final_classification is None
    assert state.next_front_wing_value is None


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

def test_car_setup_packet_updates_each_car():
    state = ApplicationState()

    packet = CarSetupPacket.from_bytes(
        make_car_setup_packet(
            next_front_wing_value=27.5,
        )
    )

    state.update(packet)

    assert state.cars[0].setup is not None
    assert state.cars[5].setup is not None
    assert state.cars[21].setup is not None

    assert state.cars[0].setup.front_wing == 0
    assert state.cars[5].setup.front_wing == 5
    assert state.cars[21].setup.front_wing == 21

    assert state.next_front_wing_value == pytest.approx(27.5)


def test_session_history_updates_correct_car():
    state = ApplicationState()

    packet = SessionHistoryPacket.from_bytes(
        make_session_history_packet(
            car_idx=7,
        )
    )

    state.update(packet)

    assert state.cars[7].session_history is packet

    assert state.cars[0].session_history is None
    assert state.cars[6].session_history is None
    assert state.cars[8].session_history is None


def test_tyre_sets_updates_correct_car():
    state = ApplicationState()

    packet = TyreSetsPacket.from_bytes(
        make_tyre_sets_packet(
            car_idx=12,
        )
    )

    state.update(packet)

    assert state.cars[12].tyre_sets is packet

    assert state.cars[0].tyre_sets is None
    assert state.cars[11].tyre_sets is None
    assert state.cars[13].tyre_sets is None

def test_lap_positions_updates_position_history():
    state = ApplicationState()

    packet = LapPositionsPacket.from_bytes(
        make_lap_positions_packet(
            num_laps=3,
            lap_start=0,
        )
    )

    state.update(packet)

    assert len(state.lap_positions) == 3

    assert state.lap_positions[0] == packet.position_for_vehicle_idx[0]

    assert state.lap_positions[1] == packet.position_for_vehicle_idx[1]

    assert state.lap_positions[2] == packet.position_for_vehicle_idx[2]

def test_lap_positions_merges_packets_using_lap_start():
    state = ApplicationState()

    first_packet = LapPositionsPacket.from_bytes(
        make_lap_positions_packet(
            num_laps=2,
            lap_start=0,
        )
    )

    second_packet = LapPositionsPacket.from_bytes(
        make_lap_positions_packet(
            num_laps=2,
            lap_start=50,
        )
    )

    state.update(first_packet)
    state.update(second_packet)

    assert set(state.lap_positions.keys()) == {0, 1, 50, 51}

    assert state.lap_positions[0] == first_packet.position_for_vehicle_idx[0]

    assert state.lap_positions[1] == first_packet.position_for_vehicle_idx[1]

    assert state.lap_positions[50] == second_packet.position_for_vehicle_idx[0]

    assert state.lap_positions[51] == second_packet.position_for_vehicle_idx[1]

def test_final_classification_updates_state():
    state = ApplicationState()

    packet = FinalClassificationPacket.from_bytes(make_final_classification_packet())

    state.update(packet)

    assert state.final_classification is packet

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

    state.lap_positions[4] = tuple(range(NUM_CARS))
    state.next_front_wing_value = 25.0

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
        assert car.setup is None
        assert car.session_history is None
        assert car.tyre_sets is None

    assert state.lap_positions == {}
    assert state.final_classification is None
    assert state.next_front_wing_value is None