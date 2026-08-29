from dataclasses import replace

import pytest

from track.builder import TrackBuilder, TrackSample, TrackPoint

from udp.constants import NUM_CARS
from udp.lap_data import LapDataPacket
from udp.motion import MotionPacket
from udp.packet_id import PacketId

from tests.helpers import make_header
from tests.udp.test_lap_data import make_lap_data_packet
from tests.udp.test_motion import make_car_motion

TRACK_LENGTH = 5000


def make_track_motion_packet(frame: int = 100) -> MotionPacket:
    """
    makes motion packet with headrs for tests
    """

    data = make_header(PacketId.MOTION, frame_identifier=frame, session_time=frame / 60.0)

    for i in range(NUM_CARS):
        data += make_car_motion(i)

    return MotionPacket.from_bytes(data)


def make_track_lap_packet(frame: int = 100) -> LapDataPacket:
    """
    makes lap data packet with headers for tests
    """

    packet = LapDataPacket.from_bytes(make_lap_data_packet())

    header = replace(
        packet.header,
        frame_identifier=frame,
        overall_frame_identifier=frame,
        session_time=frame / 60.0,
    )

    return replace(packet, header=header)


# tests

def test_builder_starts_with_no_samples():
    builder = TrackBuilder(TRACK_LENGTH)

    assert builder.samples == []


def test_process_frame_records_samples_for_all_usable_cars():
    builder = TrackBuilder(TRACK_LENGTH)

    lap_packet = make_track_lap_packet(100)
    motion_packet = make_track_motion_packet(100)

    builder.process_frame(lap_packet, motion_packet)

    assert len(builder.samples) == NUM_CARS

    first = builder.samples[0]

    assert isinstance(first, TrackSample)

    assert first.car_index == 0
    assert first.lap_number == 5
    assert first.lap_distance == pytest.approx(2000.0)

    assert first.x == pytest.approx(100.0)
    assert first.z == pytest.approx(200.0)

    last = builder.samples[21]

    assert last.car_index == 21
    assert last.lap_distance == pytest.approx(2021.0)

    assert last.x == pytest.approx(121.0)
    assert last.z == pytest.approx(221.0)


def test_process_frame_excludes_lap_zero():
    builder = TrackBuilder(TRACK_LENGTH)

    lap_packet = make_track_lap_packet(100)
    motion_packet = make_track_motion_packet(100)

    cars = list(lap_packet.cars)

    cars[3] = replace(cars[3], current_lap_num=0)

    lap_packet = replace(lap_packet, cars=tuple(cars))

    builder.process_frame(lap_packet, motion_packet)

    assert len(builder.samples) == NUM_CARS - 1

    assert all(sample.car_index != 3 for sample in builder.samples)


def test_process_frame_excludes_pit_cars():
    builder = TrackBuilder(TRACK_LENGTH)

    lap_packet = make_track_lap_packet(100)
    motion_packet = make_track_motion_packet(100)

    cars = list(lap_packet.cars)

    cars[7] = replace(cars[7],  pit_status=1)

    lap_packet = replace(lap_packet, cars=tuple(cars))

    builder.process_frame(lap_packet,motion_packet)

    assert len(builder.samples) == NUM_CARS - 1

    assert all(sample.car_index != 7 for sample in builder.samples)


def test_process_frame_excludes_non_active_cars():
    builder = TrackBuilder(TRACK_LENGTH)

    lap_packet = make_track_lap_packet(100)
    motion_packet = make_track_motion_packet(100)

    cars = list(lap_packet.cars)

    cars[12] = replace(cars[12], result_status=4)

    lap_packet = replace(lap_packet, cars=tuple(cars))

    builder.process_frame(lap_packet, motion_packet)

    assert len(builder.samples) == NUM_CARS - 1

    assert all(sample.car_index != 12 for sample in builder.samples)


def test_process_frame_appends_new_samples():
    builder = TrackBuilder(TRACK_LENGTH)

    lap_packet_1 = make_track_lap_packet(100)
    motion_packet_1 = make_track_motion_packet(100)

    lap_packet_2 = make_track_lap_packet(101)
    motion_packet_2 = make_track_motion_packet(101)

    builder.process_frame(lap_packet_1, motion_packet_1)

    assert len(builder.samples) == NUM_CARS

    builder.process_frame(lap_packet_2, motion_packet_2)

    assert len(builder.samples) == NUM_CARS * 2


def test_build_points_starts_empty():
    builder = TrackBuilder(track_length=100.0)

    points = builder.build_points()

    # 20 as 100len / 5bins = 20
    assert len(points) == 20
    assert all(point is None for point in points)


def test_build_points_creates_point_in_correct_bin():
    builder = TrackBuilder(track_length=100.0)

    builder.samples.append(
        TrackSample(
            car_index=0,
            lap_number=1,
            lap_distance=12.0,
            x=100.0,
            z=200.0,
        )
    )

    points = builder.build_points()

    point = points[2]

    assert point is not None
    assert point.distance == pytest.approx(12.5)
    assert point.x == pytest.approx(100.0)
    assert point.z == pytest.approx(200.0)

    assert sum(point is not None for point in points) == 1


def test_build_points_uses_median_position():
    builder = TrackBuilder(track_length=100.0)

    builder.samples.extend([
        TrackSample(0, 1, 11.0, 100.0, 200.0),
        TrackSample(1, 1, 12.0, 101.0, 201.0),
        TrackSample(2, 1, 13.0, 102.0, 202.0),

        # outlier
        TrackSample(3, 1, 14.0, 500.0, 700.0),
    ])

    points = builder.build_points()

    point = points[2]

    assert point is not None
    assert point.x == pytest.approx(101.5)
    assert point.z == pytest.approx(201.5)


def test_build_points_keeps_bins_separate():
    builder = TrackBuilder(track_length=100.0)

    builder.samples.extend([
        TrackSample(0, 1, 2.0, 10.0, 20.0),
        TrackSample(0, 1, 7.0, 30.0, 40.0),
        TrackSample(0, 1, 12.0, 50.0, 60.0),
    ])

    points = builder.build_points()

    assert points[0] == TrackPoint(2.5, 10.0, 20.0)
    assert points[1] == TrackPoint(7.5, 30.0, 40.0)
    assert points[2] == TrackPoint(12.5, 50.0, 60.0)


def test_build_points_ignores_negative_distance():
    builder = TrackBuilder(track_length=100.0)

    builder.samples.append(
        TrackSample(
            car_index=0,
            lap_number=1,
            lap_distance=-5.0,
            x=999.0,
            z=999.0,
        )
    )

    points = builder.build_points()

    assert all(point is None for point in points)


def test_coverage_empty():
    builder = TrackBuilder(100.0)

    coverage = builder.coverage()

    assert coverage == pytest.approx(0.0)


def test_coverage_partial():
    builder = TrackBuilder(100.0)

    builder.samples.extend([
        TrackSample(0, 1, 2.0, 10.0, 20.0),   # bin 0
        TrackSample(0, 1, 7.0, 30.0, 40.0),   # bin 1
        TrackSample(0, 1, 12.0, 50.0, 60.0),  # bin 2
    ])

    coverage = builder.coverage()

    # 3 / 20
    assert coverage == pytest.approx(0.15)


def test_coverage_full():
    builder = TrackBuilder(10.0)

    builder.samples.extend([
        TrackSample(0, 1, 2.0, 10.0, 20.0),   # bin 0
        TrackSample(0, 1, 7.0, 30.0, 40.0),   # bin 1
    ])

    coverage = builder.coverage()

    # 2/2
    assert coverage == pytest.approx(1.0)


def test_coverage_duplicate_bins():
    builder = TrackBuilder(track_length=100.0)

    builder.samples.extend([
        TrackSample(0, 1, 11.0, 100.0, 200.0),
        TrackSample(1, 1, 12.0, 101.0, 201.0),
        TrackSample(2, 1, 13.0, 102.0, 202.0),
        TrackSample(3, 1, 14.0, 103.0, 203.0),
    ])

    coverage = builder.coverage()

    # all samples lie in same bin so 1/20
    assert coverage == pytest.approx(0.05)