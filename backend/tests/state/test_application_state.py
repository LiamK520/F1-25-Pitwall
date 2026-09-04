import math
import struct

import numpy as np
import pytest
from dataclasses import replace
from types import SimpleNamespace

from track.builder import TrackSample
from state.application_state import ApplicationState, CarState
from state.history import LapTelemetryBuffer

from tests.helpers import make_header
from tests.udp.test_car_damage import make_car_damage
from tests.udp.test_event import make_event_packet
from tests.udp.test_session import make_session_packet
from tests.udp.test_car_setups import make_car_setup_packet
from tests.udp.test_session_history import make_session_history_packet
from tests.udp.test_tyre_sets import make_tyre_sets_packet
from tests.udp.test_lap_positions import make_lap_positions_packet
from tests.udp.test_final_classification import make_final_classification_packet
from tests.udp.test_lap_data import make_lap_data_packet
from tests.udp.test_car_telemetry import make_car_telemetry_packet
from tests.udp.test_motion import make_car_motion

from tests.track.test_builder import add_car_coverage

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
from udp.lap_data import LapDataPacket
from udp.car_telemetry import CarTelemetryPacket
from udp.motion import MotionPacket


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
    assert state.track_builder is None
    assert state.track_geometry is None


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

    assert state.track_builder is not None
    assert state.track_builder.track_length == 5891

    metadata = state.track_builder.metadata

    assert metadata.track_id == 7
    assert metadata.track_length == pytest.approx(5891.0)

    assert metadata.sector_2_start == pytest.approx(2000.0)
    assert metadata.sector_3_start == pytest.approx(4000.0)

    assert metadata.marshal_zone_starts == pytest.approx((
        0.10 * 5891,
        0.40 * 5891,
    ))


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

    session_packet = SessionPacket.from_bytes(make_session_packet())

    state.update(session_packet)

    assert state.track_builder is not None

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
    assert state.latest_live_frame is None
    assert state.track_builder is None
    assert state.track_geometry is None
#
# frame alignment tests
#

TEST_SESSION_UID = 123456789


def make_state_lap_packet(
    frame: int,
    lap_number: int = 1,
    lap_distance: float = 500.0,
) -> LapDataPacket:
    """
    makes LapData packet suitable for frame testing
    """

    data = make_lap_data_packet()

    packet = LapDataPacket.from_bytes(data)

    header = replace(
        packet.header,
        session_uid=TEST_SESSION_UID,
        frame_identifier=frame,
        overall_frame_identifier=frame,
        session_time=frame / 60.0,
    )

    cars = tuple(
        replace(
            lap,
            current_lap_num=lap_number,
            lap_distance=lap_distance,
        )
        for lap in packet.cars
    )

    return replace(
        packet,
        header=header,
        cars=cars,
    )


def make_state_telemetry_packet(
    frame: int,
    speed: int = 321,
) -> CarTelemetryPacket:
    """
    makes car Telemetry packet suitable for frame testing
    """

    data = make_car_telemetry_packet()

    packet = CarTelemetryPacket.from_bytes(data)

    header = replace(
        packet.header,
        session_uid=TEST_SESSION_UID,
        frame_identifier=frame,
        overall_frame_identifier=frame,
        session_time=frame / 60.0,
    )

    cars = list(packet.cars)

    cars[0] = replace(
        cars[0],
        speed=speed,
    )

    return replace(
        packet,
        header=header,
        cars=tuple(cars),
    )

def make_state_motion_packet(frame: int) -> MotionPacket:
    """
    make motion packet for frame testing
    """

    data = make_header(
        PacketId.MOTION,
        session_uid=TEST_SESSION_UID,
        session_time=frame / 60.0,
        frame_identifier=frame,
    )

    for i in range(NUM_CARS):
        data += make_car_motion(i)

    return MotionPacket.from_bytes(data)

# NOTE: If the other packets aligned by frame (e.g. motion) are later added these tests will probably need to be rewritten

def test_frame_alignment_lap_telemetry_records_sample():
    """
    Tests that the application state correctly records a telemetry sample after receiving a LapData packet and a CarTelemetry packet
    with the same overall_frame_identifier

    In this test, the state receives the LapData packet first, then the CarTelemetry packet.
    """
    state = ApplicationState()

    lap_packet = make_state_lap_packet(100, 1, 500.0)

    telemetry_packet = make_state_telemetry_packet(frame=100, speed=258)

    # lap arrival first
    state.update(lap_packet)

    # frame 100 should be in buffer
    assert 100 in state._frame_buffer

    frame_packets = state._frame_buffer[100]

    assert frame_packets.lap_data is lap_packet
    assert frame_packets.telemetry is None
    assert frame_packets.motion is None
    assert frame_packets.live_processed is False

    car = state.cars[0]

    # unmacthec packet will not affect history
    assert car.current_lap_telemetry is None

    # now telem arrives
    state.update(telemetry_packet)

    # now frame contains both
    frame_packets = state._frame_buffer[100]

    assert frame_packets.lap_data is lap_packet
    assert frame_packets.telemetry is telemetry_packet
    assert frame_packets.live_processed is True

    assert len(car.current_lap_telemetry.lap_distance) == 1
    assert car.current_lap_telemetry.lap_distance[0] == pytest.approx(500.0)
    assert car.current_lap_telemetry.speed[0] == 258


def test_frame_alignment_telemetry_lap_records_sample():
    """
    Tests that the application state correctly records a telemetry sample after receiving a LapData packet and a CarTelemetry packet
    with the same overall_frame_identifier

    In this test, the state receives the CarTelemetry packet first, then the LapData packet.
    """
        
    state = ApplicationState()

    lap_packet = make_state_lap_packet(100, 1, 600.0)

    telemetry_packet = make_state_telemetry_packet(frame=100, speed=252)

    # telem arrival first
    state.update(telemetry_packet)

    # frame 100 should be in 
    assert 100 in state._frame_buffer

    frame_packets = state._frame_buffer[100]

    assert frame_packets.lap_data is None
    assert frame_packets.telemetry is telemetry_packet
    assert frame_packets.motion is None
    assert frame_packets.live_processed is False

    car = state.cars[0]

    # now telem arrives
    state.update(lap_packet)

    frame_packets = state._frame_buffer[100]

    assert frame_packets.lap_data is lap_packet
    assert frame_packets.telemetry is telemetry_packet
    assert frame_packets.motion is None
    assert frame_packets.live_processed is True

    assert car.current_lap_telemetry is not None
    assert len(car.current_lap_telemetry.lap_distance) == 1

    assert car.current_lap_telemetry.lap_distance[0] == pytest.approx(600.0)
    assert car.current_lap_telemetry.speed[0] == 252


def test_different_frames_dont_record():
    state = ApplicationState()

    lap_packet = make_state_lap_packet(555, 3, 1232.0)
    telemetry_packet = make_state_telemetry_packet(556, 323)

    state.update(lap_packet)
    state.update(telemetry_packet)

    # both should be in buffer
    assert 555 in state._frame_buffer
    assert 556 in state._frame_buffer

    frame_555 = state._frame_buffer[555]
    frame_556 = state._frame_buffer[556]

    assert frame_555.lap_data is lap_packet
    assert frame_555.telemetry is None
    assert frame_555.live_processed is False

    assert frame_556.lap_data is None
    assert frame_556.telemetry is telemetry_packet
    assert frame_556.live_processed is False


    car = state.cars[0]

    # make sure car has no record of telem
    assert car.current_lap_telemetry is None


def test_frame_alignment_uses_matched_data():
    """
    This tests that, when aligning packets, the correct data for the frame is used, not the most recently received data (in car.lap)
    """

    state = ApplicationState()

    lap_packet = make_state_lap_packet(100, 1, 500.0)
    telemetry_packet = make_state_telemetry_packet(100)

    # store lap

    state.update(lap_packet)

    car = state.cars[0]

    assert car.lap is not None

    # create live snapshot that is different to frame 100
    car.lap = replace(car.lap, lap_distance=155.0)

    state.update(telemetry_packet)

    assert car.current_lap_telemetry is not None

    # stored sample must be from frame 100 not live sample
    assert car.current_lap_telemetry.lap_distance[0] == pytest.approx(500.0)


def test_matched_frame_before_race_does_not_create_history():
    state = ApplicationState()

    lap_packet = make_state_lap_packet(100, 0, 0.0)

    telemetry_packet = make_state_telemetry_packet(100)

    state.update(lap_packet)
    state.update(telemetry_packet)

    # lap 0 shoudlnt have telmeetry buffer

    for car in state.cars:
        assert car.current_lap_telemetry is None

    # packets matched

    assert 100 in state._frame_buffer

    frame_packets = state._frame_buffer[100]

    assert frame_packets.lap_data is lap_packet
    assert frame_packets.telemetry is telemetry_packet
    assert frame_packets.live_processed is True


def test_old_frames_removed():
    state = ApplicationState()

    lap_packet = make_state_lap_packet(100, 1)

    telemetry_packet = make_state_telemetry_packet(101)

    state.update(lap_packet)
    state.update(telemetry_packet)

    assert 100 in state._frame_buffer
    assert 101 in state._frame_buffer

    # frame 110 shoudl clear 100 out

    new_packet = make_state_lap_packet(110, 1, 505)

    state.update(new_packet)

    assert 100 not in state._frame_buffer
    assert 101 in state._frame_buffer
    assert 110 in state._frame_buffer

    # 111 should boot out 101
    newer_packet = make_state_telemetry_packet(111)

    state.update(newer_packet)

    assert 101 not in state._frame_buffer
    assert 110 in state._frame_buffer
    assert 111 in state._frame_buffer


def test_lap_change_completes_buffer():
    state = ApplicationState()

    # matched samples on lap 1
    lap_packet_1 = make_state_lap_packet(100, 1, 5000.0)
    telemetry_packet_1 = make_state_telemetry_packet(100, 250)

    state.update(lap_packet_1)
    state.update(telemetry_packet_1)

    car = state.cars[0]

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 1
    assert len(car.current_lap_telemetry.lap_distance) == 1

    # next frame crosses line so lap 2

    lap_packet_2 = make_state_lap_packet(101, 2, 5.0)
    telemetry_packet_2 = make_state_telemetry_packet(101, 255)

    state.update(lap_packet_2)
    state.update(telemetry_packet_2)

    # lap 1 done
    assert 1 in car.completed_lap_telemetry

    completed_lap = car.completed_lap_telemetry[1]

    assert len(completed_lap.lap_distance) == 1
    assert completed_lap.lap_distance[0] == pytest.approx(5000.0)
    assert completed_lap.speed[0] == 250

    # now check lap 2 is on the go
    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 2
    assert len(car.current_lap_telemetry.lap_distance) == 1
    assert car.current_lap_telemetry.lap_distance[0] == pytest.approx(5.0)
    assert car.current_lap_telemetry.speed[0] == 255


def test_unmatched_lap_data_does_not_advance_telemetry_history():
    state = ApplicationState()

    # lap 1 with one valid matched telemetry sample
    lap_packet_1 = make_state_lap_packet(
        frame=100,
        lap_number=1,
        lap_distance=5000.0,
    )
    telemetry_packet_1 = make_state_telemetry_packet(
        frame=100,
        speed=250,
    )

    state.update(lap_packet_1)
    state.update(telemetry_packet_1)

    car = state.cars[0]

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 1
    assert len(car.current_lap_telemetry.lap_distance) == 1

    #lap data for lap 2 but no matching telem
    lap_packet_2 = make_state_lap_packet(
        frame=101,
        lap_number=2,
        lap_distance=5.0,
    )

    state.update(lap_packet_2)

    # do not alter
    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 1
    assert 1 not in car.completed_lap_telemetry

    # telem arrives
    telemetry_packet_2 = make_state_telemetry_packet(
        frame=101,
        speed=255,
    )

    # do alter

    state.update(telemetry_packet_2)

    assert 1 in car.completed_lap_telemetry

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 2
    assert car.current_lap_telemetry.lap_distance == pytest.approx([5.0])
    assert car.current_lap_telemetry.speed == [255]

# test for lap telem flashback
def test_lap_telemetry_buffer_trim():
    buffer = LapTelemetryBuffer(3)

    # buffer includes out of order data
    buffer.session_time = [3.0, 6.0, 5.0, 7.0]
    buffer.lap_distance = [100.0, 250.0, 200.0, 300.0]
    buffer.speed = [180, 235, 220, 250]
    buffer.throttle = [0.5, 0.9, 0.8, 1.0]
    buffer.brake = [0.0, 0.1, 0.2, 0.0]
    buffer.steer = [0.1, -0.1, -0.2, 0.0]
    buffer.gear = [4, 5, 5, 6]
    buffer.engine_rpm = [9000, 11000, 10500, 11800]
    buffer.drs = [False, True, False, True]

    buffer.trim_after_session_time(5.0)

    # this should have removed index 1 and 3 from all above lists
    assert buffer.session_time == [3.0, 5.0]
    assert buffer.lap_distance == pytest.approx([100.0, 200.0])
    assert buffer.speed == [180, 220]
    assert buffer.throttle == pytest.approx([0.5, 0.8])
    assert buffer.brake == pytest.approx([0.0, 0.2])
    assert buffer.steer == pytest.approx([0.1, -0.2])
    assert buffer.gear == [4, 5]
    assert buffer.engine_rpm == [9000, 10500]
    assert buffer.drs == [False, False]

# helper
def packet_add_session_time(packet, session_time: float):
    return replace(packet, header=replace(packet.header, session_time=session_time))

def test_same_lap_flashback():
    state = ApplicationState()

    lap_packet_1 = make_state_lap_packet(100, 3, 1000.0)
    telemetry_packet_1 = packet_add_session_time(
        make_state_telemetry_packet(100, 200), 85.0
    )

    lap_packet_2 = make_state_lap_packet(101, 3, 1200.0)
    telemetry_packet_2 = packet_add_session_time(
        make_state_telemetry_packet(101, 220), 86.0
    )

    lap_packet_3 = make_state_lap_packet(102, 3, 1400.0)
    telemetry_packet_3 = packet_add_session_time(
        make_state_telemetry_packet(102, 240), 87.0
    )

    # this order is fine as same lap and no risk of htting frame limit for del
    state.update(lap_packet_1)
    state.update(lap_packet_2)
    state.update(lap_packet_3)

    state.update(telemetry_packet_1)
    state.update(telemetry_packet_2)
    state.update(telemetry_packet_3)

    car = state.cars[0]

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.session_time == pytest.approx([85.0, 86.0, 87.0])

    # flashback between second and third entry

    flashback_packet = EventPacket.from_bytes(make_event_packet(
        "FLBK", struct.pack("<If", 900, 86.5)
    ))

    state.update(flashback_packet)

    assert state._pending_flashback_time == pytest.approx(86.5)
    assert state._pending_flashback_frame == 900

    # now new lap data inbound, same lap

    lap_packet_4 = make_state_lap_packet(103, 3, 1250.0)

    state.update(lap_packet_4)

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 3

    assert car.current_lap_telemetry.session_time == pytest.approx([85.0, 86.0])
    assert car.current_lap_telemetry.lap_distance == pytest.approx([1000.0, 1200.0])
    assert car.current_lap_telemetry.speed == [200, 220]

    # flashback done
    assert state._pending_flashback_frame is None
    assert state._pending_flashback_time is None

    # now match tleemetry to check that recording continues
    telemetry_packet_4 = packet_add_session_time(make_state_telemetry_packet(103, 225), 86.6)

    state.update(telemetry_packet_4)

    assert car.current_lap_telemetry.session_time == pytest.approx([85.0, 86.0, 86.6])
    assert car.current_lap_telemetry.lap_distance == pytest.approx([1000.0, 1200.0, 1250.0])
    assert car.current_lap_telemetry.speed == [200, 220, 225]


def test_lap_telemetry_to_buffer():
    buffer = LapTelemetryBuffer(7)

    buffer.session_time = [100.0, 100.1, 100.2]
    buffer.lap_distance = [1200.0, 1225.0, 1250.0]

    buffer.speed = [245, 252, 258]
    buffer.throttle = [0.7, 0.9, 1.0]
    buffer.brake = [0.2, 0.0, 0.0]
    buffer.steer = [-0.15, -0.05, 0.0]

    buffer.gear = [5, 6, 6]
    buffer.engine_rpm = [10500, 11200, 11800]

    buffer.drs = [False, False, True]

    lap_telem = buffer.finish()

    # ensure that setup is corect

    # sanity check that all the lap_telem attrs are np arays and not lists
    assert isinstance(lap_telem.session_time, np.ndarray)
    assert isinstance(lap_telem.lap_distance, np.ndarray)
    assert isinstance(lap_telem.speed, np.ndarray)
    assert isinstance(lap_telem.throttle, np.ndarray)
    assert isinstance(lap_telem.brake, np.ndarray)
    assert isinstance(lap_telem.steer, np.ndarray)
    assert isinstance(lap_telem.gear, np.ndarray)
    assert isinstance(lap_telem.engine_rpm, np.ndarray)
    assert isinstance(lap_telem.drs, np.ndarray)

    # now ensure vals are correct
    np.testing.assert_allclose(lap_telem.session_time, [100.0, 100.1, 100.2])
    np.testing.assert_allclose(lap_telem.lap_distance, [1200.0, 1225.0, 1250.0])

    np.testing.assert_array_equal(lap_telem.speed, [245, 252, 258])
    np.testing.assert_allclose(lap_telem.throttle, [0.7, 0.9, 1.0])
    np.testing.assert_allclose(lap_telem.brake, [0.2, 0.0, 0.0])
    np.testing.assert_allclose(lap_telem.steer, [-0.15, -0.05, 0.0])

    np.testing.assert_array_equal(lap_telem.gear, [5, 6, 6])
    np.testing.assert_array_equal(lap_telem.engine_rpm, [10500, 11200, 11800])
    np.testing.assert_array_equal(lap_telem.drs, [False, False, True])

    # this is the actual test

    new_buffer = lap_telem.to_buffer()

    assert new_buffer.lap_number == 7

    # now they should be back to original lists
    assert isinstance(new_buffer.session_time, list)
    assert isinstance(new_buffer.lap_distance, list)
    assert isinstance(new_buffer.speed, list)
    assert isinstance(new_buffer.throttle, list)
    assert isinstance(new_buffer.brake, list)
    assert isinstance(new_buffer.steer, list)
    assert isinstance(new_buffer.gear, list)
    assert isinstance(new_buffer.engine_rpm, list)
    assert isinstance(new_buffer.drs, list)

    assert new_buffer.session_time == pytest.approx([100.0, 100.1, 100.2])
    assert new_buffer.lap_distance == pytest.approx([1200.0, 1225.0, 1250.0])

    assert new_buffer.speed == [245, 252, 258]
    assert new_buffer.throttle == pytest.approx([0.7, 0.9, 1.0])
    assert new_buffer.brake == pytest.approx([0.2, 0.0, 0.0])
    assert new_buffer.steer == pytest.approx([-0.15, -0.05, 0.0])

    assert new_buffer.gear == [5, 6, 6]
    assert new_buffer.engine_rpm == [10500, 11200, 11800]

    assert new_buffer.drs == [False, False, True]


def test_different_lap_flashback():
    state = ApplicationState()

    lap_packet_1 = make_state_lap_packet(100, 3, 1000.0)
    telemetry_packet_1 = packet_add_session_time(
        make_state_telemetry_packet(100, 200), 85.0
    )

    lap_packet_2 = make_state_lap_packet(101, 3, 1200.0)
    telemetry_packet_2 = packet_add_session_time(
        make_state_telemetry_packet(101, 220), 86.0
    )

    lap_packet_3 = make_state_lap_packet(102, 4, 100.0)
    telemetry_packet_3 = packet_add_session_time(
        make_state_telemetry_packet(102, 240), 87.0
    )

    state.update(lap_packet_1)
    state.update(telemetry_packet_1)

    state.update(lap_packet_2)
    state.update(telemetry_packet_2)

    state.update(lap_packet_3)
    state.update(telemetry_packet_3)

    car = state.cars[0]

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 4
    assert car.current_lap_telemetry.session_time == pytest.approx([87.0])

    assert car.completed_lap_telemetry is not None
    assert 3 in car.completed_lap_telemetry
    np.testing.assert_allclose(car.completed_lap_telemetry[3].session_time, [85.0, 86.0])

    # flashback between second and third entry, crossing lap 3/4

    flashback_packet = EventPacket.from_bytes(make_event_packet(
        "FLBK", struct.pack("<If", 102, 85.5)
    ))

    state.update(flashback_packet)

    assert state._pending_flashback_time == pytest.approx(85.5)
    assert state._pending_flashback_frame == 102

    # now new lap data inbound, lap 3

    lap_packet_4 = make_state_lap_packet(103, 3, 1200.0)
    state.update(lap_packet_4)

    assert 3 not in car.completed_lap_telemetry

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 3
    assert car.current_lap_telemetry.session_time == pytest.approx([85.0])
    assert car.current_lap_telemetry.lap_distance == pytest.approx([1000.0])
    assert car.current_lap_telemetry.speed == [200]

    assert state._pending_flashback_time is None
    assert state._pending_flashback_frame is None

    telemetry_packet_4 = packet_add_session_time(
        make_state_telemetry_packet(103, 238), 85.6
    )

    state.update(telemetry_packet_4)

    assert car.current_lap_telemetry.session_time == pytest.approx([85.0, 85.6])
    assert car.current_lap_telemetry.lap_distance == pytest.approx([1000.0, 1200.0])
    assert car.current_lap_telemetry.speed == [200, 238]

def test_flashback_to_lap_zero():
    """
    Tests that, upon receiving a flashback to lap 0, no new telemetry buffer is created
    """
    state = ApplicationState()

    lap_packet_1 = make_state_lap_packet(4, 1, 10.0)
    telemetry_packet_1 = packet_add_session_time(
        make_state_telemetry_packet(4, 24), 15.0
    )

    state.update(lap_packet_1)

    state.update(telemetry_packet_1)


    car = state.cars[0]

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.session_time == pytest.approx([15.0])

    # flashback to lap 0

    flashback_packet = EventPacket.from_bytes(make_event_packet(
        "FLBK", struct.pack("<If", 0, 0.0)
    ))

    state.update(flashback_packet)

    assert state._pending_flashback_time == pytest.approx(0.0)
    assert state._pending_flashback_frame == 0

    # now new lap data but for lap 0

    lap_packet_2 = make_state_lap_packet(5, 0, 0.0)

    state.update(lap_packet_2)

    assert car.current_lap_telemetry is  None
    assert state._pending_flashback_frame is None
    assert state._pending_flashback_time is None


def test_flashback_across_multiple_laps():
    """
    This tests that a flashback spanning multiple laps deletes completed laps correctly and restarts the correct buffer
    """
    state = ApplicationState()
    
    lap_packet_1 = make_state_lap_packet(100, 3, 1000.0)
    telemetry_packet_1 = packet_add_session_time(
        make_state_telemetry_packet(100, 200), 85.0
    )

    lap_packet_2 = make_state_lap_packet(101, 4, 1200.0)
    telemetry_packet_2 = packet_add_session_time(
        make_state_telemetry_packet(101, 220), 86.0
    )

    lap_packet_3 = make_state_lap_packet(102, 5, 100.0)
    telemetry_packet_3 = packet_add_session_time(
        make_state_telemetry_packet(102, 240), 87.0
    )

    state.update(lap_packet_1)
    state.update(telemetry_packet_1)

    state.update(lap_packet_2)
    state.update(telemetry_packet_2)

    state.update(lap_packet_3)
    state.update(telemetry_packet_3)

    car = state.cars[0]

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 5
    assert car.current_lap_telemetry.session_time == pytest.approx([87.0])

    assert car.completed_lap_telemetry is not None
    assert 3 in car.completed_lap_telemetry
    assert 4 in car.completed_lap_telemetry
    np.testing.assert_allclose(car.completed_lap_telemetry[3].session_time, [85.0])
    np.testing.assert_allclose(car.completed_lap_telemetry[4].session_time, [86.0])

    # flashback between second and third entry, crossing lap 3/4/5

    flashback_packet = EventPacket.from_bytes(make_event_packet(
        "FLBK", struct.pack("<If", 102, 85.5)
    ))

    # should be a amtch
    assert state.latest_live_frame is not None
    
    state.update(flashback_packet)


    # match discard after flashback
    assert state.latest_live_frame is None

    assert state._pending_flashback_time == pytest.approx(85.5)
    assert state._pending_flashback_frame == 102

    # now new lap data inbound, lap 3
    # laps 3-5 no longer in completed, lap 3 reopened

    lap_packet_4 = make_state_lap_packet(103, 3, 1200.0)
    state.update(lap_packet_4)

    assert 3 not in car.completed_lap_telemetry
    assert 4 not in car.completed_lap_telemetry
    assert 5 not in car.completed_lap_telemetry

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 3
    assert car.current_lap_telemetry.session_time == pytest.approx([85.0])
    assert car.current_lap_telemetry.lap_distance == pytest.approx([1000.0])
    assert car.current_lap_telemetry.speed == [200]

    assert state._pending_flashback_time is None
    assert state._pending_flashback_frame is None

    telemetry_packet_4 = packet_add_session_time(
        make_state_telemetry_packet(103, 238), 85.6
    )

    state.update(telemetry_packet_4)

    assert car.current_lap_telemetry.session_time == pytest.approx([85.0, 85.6])
    assert car.current_lap_telemetry.lap_distance == pytest.approx([1000.0, 1200.0])
    assert car.current_lap_telemetry.speed == [200, 238]


def test_target_not_recorded():
    """
    This tests that flashbacks to laps that dont have a recorded sample just get a new buffer.
    """

    state = ApplicationState()

    lap_packet_1 = make_state_lap_packet(100, 3, 1000.0)
    telemetry_packet_1 = packet_add_session_time(
        make_state_telemetry_packet(100, 200), 85.0
    )

    lap_packet_2 = make_state_lap_packet(101, 3, 1200.0)
    telemetry_packet_2 = packet_add_session_time(
        make_state_telemetry_packet(101, 220), 86.0
    )

    lap_packet_3 = make_state_lap_packet(102, 3, 1400.0)
    telemetry_packet_3 = packet_add_session_time(
        make_state_telemetry_packet(102, 240), 87.0
    )

    # this order is fine as same lap and no risk of htting frame limit for del
    state.update(lap_packet_1)
    state.update(lap_packet_2)
    state.update(lap_packet_3)

    state.update(telemetry_packet_1)
    state.update(telemetry_packet_2)
    state.update(telemetry_packet_3)

    car = state.cars[0]

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.session_time == pytest.approx([85.0, 86.0, 87.0])

    # flashback between second and third entry

    flashback_packet = EventPacket.from_bytes(make_event_packet(
        "FLBK", struct.pack("<If", 900, 86.5)
    ))

    state.update(flashback_packet)

    assert state._pending_flashback_time == pytest.approx(86.5)
    assert state._pending_flashback_frame == 900

    # now new lap data inbound, this time to lap 2, unrecorded

    lap_packet_4 = make_state_lap_packet(103, 2, 1250.0)

    state.update(lap_packet_4)

    assert car.current_lap_telemetry is not None
    assert car.current_lap_telemetry.lap_number == 2
    assert 3 not in car.completed_lap_telemetry

    # flashback done
    assert state._pending_flashback_frame is None
    assert state._pending_flashback_time is None

    # now match tleemetry to check that recording continues
    telemetry_packet_4 = packet_add_session_time(make_state_telemetry_packet(103, 225), 86.6)

    state.update(telemetry_packet_4)

    assert car.current_lap_telemetry.session_time == pytest.approx([86.6])
    assert car.current_lap_telemetry.lap_distance == pytest.approx([1250.0])
    assert car.current_lap_telemetry.speed == [225]  


def test_flashback_in_event_log():
    """
    Tests that flashbacks are correctly added to event log, including after the flashback is handled
    """
    state = ApplicationState()

    lap_packet_1 = make_state_lap_packet(100, 3, 1000.0)
    telemetry_packet_1 = packet_add_session_time(
        make_state_telemetry_packet(100, 200), 85.0
    )

    lap_packet_2 = make_state_lap_packet(101, 3, 1200.0)
    telemetry_packet_2 = packet_add_session_time(
        make_state_telemetry_packet(101, 220), 86.0
    )

    # this order is fine as same lap and no risk of htting frame limit for del
    state.update(lap_packet_1)
    state.update(lap_packet_2)

    state.update(telemetry_packet_1)
    state.update(telemetry_packet_2)

    # skipping buffer assertions as these are validating in previous tests

    # flashback between second and third entry

    flashback_packet = EventPacket.from_bytes(make_event_packet(
        "FLBK", struct.pack("<If", 900, 86.5)
    ))

    state.update(flashback_packet)

    assert state._pending_flashback_time == pytest.approx(86.5)
    assert state._pending_flashback_frame == 900
    assert flashback_packet in state.events

    # now do flashback

    lap_packet_4 = make_state_lap_packet(103, 3, 1250.0)

    state.update(lap_packet_4)

    # flashback done, esure packet still in event log
    assert state._pending_flashback_frame is None
    assert state._pending_flashback_time is None
    assert flashback_packet in state.events


def test_latest_live_frame_starts_none():
    state = ApplicationState()

    assert state.latest_live_frame is None


def test_matched_packets_create_latest_live_frame():
    state = ApplicationState()

    lap_packet = make_state_lap_packet(100, 3, 1250.0)

    telemetry_packet = make_state_telemetry_packet(100, 250)

    state.update(lap_packet)

    # no match
    assert state.latest_live_frame is None

    state.update(telemetry_packet)

    # yes match
    assert state.latest_live_frame is not None

    assert state.latest_live_frame.overall_frame_identifier == 100
    assert state.latest_live_frame.lap_data is lap_packet
    assert state.latest_live_frame.telemetry is telemetry_packet
    assert state.latest_live_frame.session_time == pytest.approx(lap_packet.header.session_time)


def test_unmatched_packets_do_not_create_latest_live_frame():
    state = ApplicationState()

    lap_packet = make_state_lap_packet(100, 3, 1250.0)

    telemetry_packet = make_state_telemetry_packet(101, 250)

    state.update(lap_packet)
    state.update(telemetry_packet)

    assert state.latest_live_frame is None


def test_new_match_replaces_latest_live_frame():
    state = ApplicationState()

    lap_packet_1 = make_state_lap_packet(100, 3, 1200.0)

    telemetry_packet_1 = make_state_telemetry_packet(100, 240)

    state.update(lap_packet_1)
    state.update(telemetry_packet_1)

    first_frame = state.latest_live_frame

    assert first_frame is not None
    assert first_frame.overall_frame_identifier == 100

    lap_packet_2 = make_state_lap_packet(101, 3, 1250.0)

    telemetry_packet_2 = make_state_telemetry_packet(101, 250)

    state.update(lap_packet_2)
    state.update(telemetry_packet_2)

    assert state.latest_live_frame is not None
    assert state.latest_live_frame.overall_frame_identifier == 101

    assert state.latest_live_frame is not first_frame
    assert state.latest_live_frame.lap_data is lap_packet_2
    assert state.latest_live_frame.telemetry is telemetry_packet_2


def test_motion_packet_updates_latest_motion():
    state = ApplicationState()

    packet = make_state_motion_packet(100)

    state.update(packet)

    assert state.latest_motion is packet

    for i in range(NUM_CARS):
        assert state.cars[i].motion is packet.cars[i]

    state.reset()

    assert state.latest_motion is None


def test_frame_buffer_groups_packet():
    state = ApplicationState()

    state.update(SessionPacket.from_bytes(make_session_packet()))

    assert state.track_builder is not None

    lap_packet = make_state_lap_packet(100, 1, 500.0)
    telemetry_packet = make_state_telemetry_packet(100, 250)
    motion_packet = make_state_motion_packet(100)

    state.update(lap_packet)
    state.update(telemetry_packet)
    state.update(motion_packet)

    assert 100 in state._frame_buffer

    frame_packets = state._frame_buffer[100]

    assert frame_packets.lap_data is lap_packet
    assert frame_packets.telemetry is telemetry_packet
    assert frame_packets.motion is motion_packet

    assert frame_packets.live_processed is True
    assert frame_packets.track_processed is True


def test_late_motion_does_not_reprocess_live_frame():
    state = ApplicationState()

    lap_packet = make_state_lap_packet(100, 1, 500.0)
    telemetry_packet = make_state_telemetry_packet(100, 250)
    motion_packet = make_state_motion_packet(100)

    state.update(lap_packet)
    state.update(telemetry_packet)

    car = state.cars[0]

    assert car.current_lap_telemetry is not None
    assert len(car.current_lap_telemetry.lap_distance) == 1

    # motion inbound so frame 100 is handled again
    state.update(motion_packet)

    # make sure we dont process telem stuff again
    assert len(car.current_lap_telemetry.lap_distance) == 1

    frame_packets = state._frame_buffer[100]

    assert frame_packets.live_processed is True
    assert frame_packets.motion is motion_packet


def test_lap_motion_pair_records_track_samples():
    state = ApplicationState()

    state.update(SessionPacket.from_bytes(make_session_packet()))

    assert state.track_builder is not None

    lap_packet = make_state_lap_packet(frame=100, lap_number=1, lap_distance=500.0)

    motion_packet = make_state_motion_packet(100)

    state.update(lap_packet)

    assert len(state.track_builder.samples) == 0

    # complete track pair
    state.update(motion_packet)

    assert len(state.track_builder.samples) == NUM_CARS

    frame_packets = state._frame_buffer[100]

    assert frame_packets.track_processed is True

    first = state.track_builder.samples[0]

    assert first.car_index == 0
    assert first.lap_number == 1
    assert first.lap_distance == pytest.approx(500.0)

    assert first.x == pytest.approx(motion_packet.cars[0].world_position_x)

    assert first.z == pytest.approx(motion_packet.cars[0].world_position_z)


def test_track_frame_is_only_processed_once():
    state = ApplicationState()

    state.update(SessionPacket.from_bytes(make_session_packet()))

    assert state.track_builder is not None

    lap_packet = make_state_lap_packet(frame=100, lap_number=1, lap_distance=500.0)

    motion_packet = make_state_motion_packet(100)
    telemetry_packet = make_state_telemetry_packet(100)

    state.update(lap_packet)
    state.update(motion_packet)

    assert len(state.track_builder.samples) == NUM_CARS

    # consider frame again
    state.update(telemetry_packet)

    # ensure we dont process that sample again
    assert len(state.track_builder.samples) == NUM_CARS

    assert state._frame_buffer[100].track_processed is True


def test_track_builder_finalises():
    state = ApplicationState()

    state.update(SessionPacket.from_bytes(make_session_packet()))

    assert state.track_builder is not None
    assert state.track_geometry is None

    builder = state.track_builder

    # fiall bins
    # same logic as
    num_bins = math.ceil(builder.track_length / builder.BIN_SIZE)

    add_car_coverage(builder, num_bins, num_cars=builder.MIN_FINALISE_CARS)

    assert builder.ready_to_finalise()

    # process matched track frame to trigger try_process_frame
    state.update(make_state_lap_packet(frame=100))
    state.update(make_state_motion_packet(frame=100))

    assert state.track_geometry is not None

    assert state.track_geometry.track_id == builder.metadata.track_id
    assert state.track_geometry.track_length == builder.metadata.track_length


def test_track_builder_stops_after_finalise():
    state = ApplicationState()

    state.update(SessionPacket.from_bytes(make_session_packet()))

    assert state.track_builder is not None

    builder = state.track_builder

    num_bins = math.ceil(builder.track_length / builder.BIN_SIZE)

    add_car_coverage(builder, num_bins=num_bins, num_cars=builder.MIN_FINALISE_CARS)

    # finalsie
    state.update(make_state_lap_packet(frame=100))
    state.update(make_state_motion_packet(frame=100))

    assert state.track_geometry is not None

    sample_count = len(builder.samples)

    # another matched frame
    state.update(make_state_lap_packet(frame=101))
    state.update(make_state_motion_packet(frame=101))

    # should not impact samples
    assert len(builder.samples) == sample_count


def test_session_updates_track_builder_metadata():
    """
    This tests that each session packet updates metadata.

    Added this test because F1 25 seems to send initial session packets with 0 marshall zones, but all subsequent ones have x amount,
    leading to the track builder storing an incorrect marshal zone tuple
    """

    state = ApplicationState()

    # existing helper contains 2 marshal zones at 0.10 and 0.40
    packet_with_zones = SessionPacket.from_bytes(make_session_packet())

    # remove them to test early packet without zones
    packet_without_zones = replace(packet_with_zones, num_marshal_zones=0, marshal_zones=())

    state.update(packet_without_zones)

    assert state.track_builder is not None

    builder = state.track_builder

    assert builder.metadata.marshal_zone_starts == ()

    # later packet that has zones
    state.update(packet_with_zones)

    # make sure our builder is still our builder and not a phony
    assert state.track_builder is builder

    # and finally we make sure that there is the zones again
    assert builder.metadata.marshal_zone_starts == pytest.approx((
        0.10 * packet_with_zones.track_length,
        0.40 * packet_with_zones.track_length,
    ))