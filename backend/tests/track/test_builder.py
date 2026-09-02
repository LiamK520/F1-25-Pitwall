from dataclasses import replace

import pytest

from track.builder import TrackBuilder, TrackSample
from track.geometry import TrackPoint, TrackMetadata, TrackGeometry

from udp.constants import NUM_CARS
from udp.lap_data import LapDataPacket
from udp.motion import MotionPacket
from udp.packet_id import PacketId

from tests.helpers import make_header
from tests.udp.test_lap_data import make_lap_data_packet
from tests.udp.test_motion import make_car_motion

TRACK_LENGTH = 5000


# helper for coverage
def add_car_coverage(builder: TrackBuilder, num_bins: int, num_cars: int) -> None:
    for bin_index in range(num_bins):
        dist = bin_index * builder.BIN_SIZE + 1.0

        for car_index in range(num_cars):
            builder.samples.append(TrackSample(
                car_index=car_index,
                lap_number=1,
                lap_distance=dist,
                x=dist,
                z=dist
            ))


def make_track_metadata(track_length: int = TRACK_LENGTH) -> TrackMetadata:
    return TrackMetadata(
        track_id=7,
        track_length=track_length,
        sector_2_start=track_length * 0.3,
        sector_3_start=track_length * 0.7,
        marshal_zone_starts=(track_length * 0.15, track_length * 0.85),
    )


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
    builder = TrackBuilder(make_track_metadata())

    assert builder.samples == []


def test_process_frame_records_samples_for_all_usable_cars():
    builder = TrackBuilder(make_track_metadata())

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
    builder = TrackBuilder(make_track_metadata())

    lap_packet = make_track_lap_packet(100)
    motion_packet = make_track_motion_packet(100)

    cars = list(lap_packet.cars)

    cars[3] = replace(cars[3], current_lap_num=0)

    lap_packet = replace(lap_packet, cars=tuple(cars))

    builder.process_frame(lap_packet, motion_packet)

    assert len(builder.samples) == NUM_CARS - 1

    assert all(sample.car_index != 3 for sample in builder.samples)


def test_process_frame_excludes_pit_cars():
    builder = TrackBuilder(make_track_metadata())

    lap_packet = make_track_lap_packet(100)
    motion_packet = make_track_motion_packet(100)

    cars = list(lap_packet.cars)

    cars[7] = replace(cars[7],  pit_status=1)

    lap_packet = replace(lap_packet, cars=tuple(cars))

    builder.process_frame(lap_packet,motion_packet)

    assert len(builder.samples) == NUM_CARS - 1

    assert all(sample.car_index != 7 for sample in builder.samples)


def test_process_frame_excludes_non_active_cars():
    builder = TrackBuilder(make_track_metadata())

    lap_packet = make_track_lap_packet(100)
    motion_packet = make_track_motion_packet(100)

    cars = list(lap_packet.cars)

    cars[12] = replace(cars[12], result_status=4)

    lap_packet = replace(lap_packet, cars=tuple(cars))

    builder.process_frame(lap_packet, motion_packet)

    assert len(builder.samples) == NUM_CARS - 1

    assert all(sample.car_index != 12 for sample in builder.samples)


def test_process_frame_appends_new_samples():
    builder = TrackBuilder(make_track_metadata())

    lap_packet_1 = make_track_lap_packet(100)
    motion_packet_1 = make_track_motion_packet(100)

    lap_packet_2 = make_track_lap_packet(101)
    motion_packet_2 = make_track_motion_packet(101)

    builder.process_frame(lap_packet_1, motion_packet_1)

    assert len(builder.samples) == NUM_CARS

    builder.process_frame(lap_packet_2, motion_packet_2)

    assert len(builder.samples) == NUM_CARS * 2


def test_build_points_starts_empty():
    builder = TrackBuilder(make_track_metadata(100))

    points = builder.build_points()

    # 20 as 100len / 5bins = 20
    assert len(points) == 20
    assert all(point is None for point in points)


def test_build_points_creates_point_in_correct_bin():
    builder = TrackBuilder(make_track_metadata(100))

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
    builder = TrackBuilder(make_track_metadata(100))

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
    builder = TrackBuilder(make_track_metadata(100))

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
    builder = TrackBuilder(make_track_metadata(100))

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


def test_build_points_ignores_dist_gt_len():
    # dist > len should not be possible so the bin should not be created and sample not stored
    builder = TrackBuilder(make_track_metadata(100))

    builder.samples.append(TrackSample(
        car_index=0,
        lap_number=1,
        lap_distance=105.0,
        x=999.0,
        z=999.0
    ))

    points = builder.build_points()

    assert all(point is None for point in points)

def test_coverage_empty():
    builder = TrackBuilder(make_track_metadata(100))

    coverage = builder.coverage()

    assert coverage == pytest.approx(0.0)


def test_coverage_partial():
    builder = TrackBuilder(make_track_metadata(100))

    builder.samples.extend([
        TrackSample(0, 1, 2.0, 10.0, 20.0),   # bin 0
        TrackSample(0, 1, 7.0, 30.0, 40.0),   # bin 1
        TrackSample(0, 1, 12.0, 50.0, 60.0),  # bin 2
    ])

    coverage = builder.coverage()

    # 3 / 20
    assert coverage == pytest.approx(0.15)


def test_coverage_full():
    builder = TrackBuilder(make_track_metadata(10))

    builder.samples.extend([
        TrackSample(0, 1, 2.0, 10.0, 20.0),   # bin 0
        TrackSample(0, 1, 7.0, 30.0, 40.0),   # bin 1
    ])

    coverage = builder.coverage()

    # 2/2
    assert coverage == pytest.approx(1.0)


def test_coverage_duplicate_bins():
    builder = TrackBuilder(make_track_metadata(100))

    builder.samples.extend([
        TrackSample(0, 1, 11.0, 100.0, 200.0),
        TrackSample(1, 1, 12.0, 101.0, 201.0),
        TrackSample(2, 1, 13.0, 102.0, 202.0),
        TrackSample(3, 1, 14.0, 103.0, 203.0),
    ])

    coverage = builder.coverage()

    # all samples lie in same bin so 1/20
    assert coverage == pytest.approx(0.05)


def test_sample_coutns():
    builder = TrackBuilder(make_track_metadata(20))

    builder.samples.extend([
        TrackSample(0, 1, 1.0, 10.0, 20.0),
        TrackSample(1, 1, 2.0, 11.0, 21.0),
        TrackSample(2, 1, 7.0, 12.0, 22.0),
    ])

    assert builder.sample_counts() == [2, 1, 0, 0]


def test_car_counts_only_counts_unique_cars():
    builder = TrackBuilder(make_track_metadata(20))

    builder.samples.extend([
        TrackSample(0, 1, 1.0, 10.0, 20.0),
        TrackSample(0, 1, 2.0, 11.0, 21.0),
        TrackSample(3, 1, 3.0, 12.0, 22.0),
        TrackSample(5, 1, 7.0, 13.0, 23.0),
    ])

    # 3 samples in bin 1 but only 2 cars
    assert builder.car_counts() == [2, 1, 0, 0]


def test_ready_to_finalise_requires_car_coverage():
    builder = TrackBuilder(make_track_metadata(500))

    # cover all bins with 1 car only
    add_car_coverage(builder, num_bins=100, num_cars=1)

    assert builder.coverage() == pytest.approx(1.0)
    assert builder.ready_to_finalise() is False


def test_ready_to_finalise_requirement_met():
    builder = TrackBuilder(make_track_metadata(500))

    # 10 cars, 99% coverage. bang on goal
    add_car_coverage(builder, num_bins=99, num_cars=10)

    # still need raw coverage for final bin but less than 10
    builder.samples.append(TrackSample(
        car_index=0,
        lap_number=1,
        lap_distance=496.0,
        x=496.0,
        z=496.0
    ))

    assert builder.coverage() == pytest.approx(1.0)
    assert builder.car_coverage(10) == pytest.approx(0.99)
    assert builder.ready_to_finalise() is True

def test_ready_to_finalise_requirement_not_met():
    builder = TrackBuilder(make_track_metadata(5000))

    # 10 cars, 98.9% coverage just under goal
    add_car_coverage(builder, num_bins=989, num_cars=10)

    #  this fills all dists for last 11 bins
    for distance in range(4446, 4997, 5):
        builder.samples.append(TrackSample(
                car_index=0,
                lap_number=1,
                lap_distance=distance,
                x=distance,
                z=distance,
            ))

    assert builder.coverage() == pytest.approx(1.0)
    assert builder.car_coverage(10) == pytest.approx(0.989)
    assert builder.ready_to_finalise() is False


def test_ready_to_finalise_coverage_not_met():
    builder = TrackBuilder(make_track_metadata(500))
    
    # 10 cars, 99% coverage. bang on goal
    add_car_coverage(builder, num_bins=99, num_cars=10)

    # no extra coverage this time
    assert builder.coverage() == pytest.approx(0.99)
    assert builder.car_coverage(10) == pytest.approx(0.99)
    assert builder.ready_to_finalise() is False


def test_finalise_reject_incomplete():
    builder = TrackBuilder(make_track_metadata())

    with pytest.raises(RuntimeError):
        builder.finalise()


def test_finalise_accepts_complete():
    builder = TrackBuilder(make_track_metadata(track_length=500))

    # 100 bins, all with 10 cars
    add_car_coverage(builder, num_bins=100, num_cars=10)

    geometry = builder.finalise()

    assert isinstance(geometry, TrackGeometry)

    assert geometry.track_id == builder.metadata.track_id
    assert geometry.track_length == 500

    assert geometry.sector_2_start == builder.metadata.sector_2_start
    assert geometry.sector_3_start == builder.metadata.sector_3_start
    assert geometry.marshal_zone_starts == builder.metadata.marshal_zone_starts

    # 100 points + 2 marshal zones and 2 sector
    assert len(geometry.points) == 105


def test_finalise_correct_bounds():
    builder = builder = TrackBuilder(make_track_metadata(track_length=500))

    add_car_coverage(builder, num_bins=100, num_cars=10)

    geometry = builder.finalise()

    # helper sticks bins at 1, 6 etc. up to 496 for both x and z
    assert geometry.min_x == pytest.approx(1.0)
    assert geometry.max_x == pytest.approx(496.0)

    assert geometry.min_z == pytest.approx(1.0)
    assert geometry.max_z == pytest.approx(496.0)


def test_interploate_midpoint():
    builder = TrackBuilder(make_track_metadata())

    point1 = TrackPoint(10, 20, 50)
    point2 = TrackPoint(20, 30, 10)

    point3 = builder._interpolate_point(point1, point2, 15)

    assert point3.distance == 15
    assert point3.x == pytest.approx(25)
    assert point3.z == pytest.approx(30)


def test_interpolate_not_midpoint():
    builder = TrackBuilder(make_track_metadata())

    point1 = TrackPoint(100, 320, 80)
    point2 = TrackPoint(500, 60, 180)

    # 400 = 75%
    point3 = builder._interpolate_point(point1, point2, 400)

    assert point3.distance == pytest.approx(400.0)
    # 320 - 60 = 260 * 0.25 = 65, 60 _ 65 = 125
    assert point3.x == pytest.approx(125)
    # 180 - 80 = 100 * 0.25 = 25, 180 - 25 = 155
    assert point3.z == pytest.approx(155)


def test_interpolate_wraparound_before():
    builder = TrackBuilder(make_track_metadata(100.0))

    point1 = TrackPoint(95, 20, 30)
    point2 = TrackPoint(5, 40, 0)

    point3 = builder._interpolate_wraparound_point(point1, point2, 0.0)

    assert point3.distance == pytest.approx(0.0)
    assert point3.x == pytest.approx(30.0)
    assert point3.z == pytest.approx(15.0)


def test_interpolate_wraparound_after():
    builder = TrackBuilder(make_track_metadata(100.0))

    point1 = TrackPoint(95, 20, 30)
    point2 = TrackPoint(5, 40, 0)

    point3 = builder._interpolate_wraparound_point(point1, point2, 100.0)

    assert point3.distance == pytest.approx(100.0)
    assert point3.x == pytest.approx(30.0)
    assert point3.z == pytest.approx(15.0)

def test_insert_point_between_points():
    builder = TrackBuilder(make_track_metadata())

    points = [
        TrackPoint(10, 20, 50),
        TrackPoint(20, 30, 10),
        TrackPoint(30, 40, 30),
    ]


    builder._insert_point_at_distance(points, 15)
    assert [point.distance for point in points] == [10, 15, 20, 30]

    inserted = points[1]

    assert inserted.distance == pytest.approx(15)
    assert inserted.x == pytest.approx(25)
    assert inserted.z == pytest.approx(30)


def test_insert_point_does_not_duplicate_existing_distance():
    builder = TrackBuilder(make_track_metadata())

    points = [
        TrackPoint(10, 20, 50),
        TrackPoint(20, 30, 10),
        TrackPoint(30, 40, 30),
    ]

    builder._insert_point_at_distance(points, 20)

    assert len(points) == 3

    assert [point.distance for point in points] == [10, 20, 30]


def test_insert_point_between_final_pair():
    builder = TrackBuilder(make_track_metadata())

    points = [
        TrackPoint(10, 20, 50),
        TrackPoint(20, 30, 10),
        TrackPoint(30, 40, 30),
    ]

    builder._insert_point_at_distance(points, 25)

    assert [point.distance for point in points] == [10, 20, 25, 30]

    inserted = points[2]

    assert inserted.distance == pytest.approx(25)

    assert inserted.x == pytest.approx(35)
    assert inserted.z == pytest.approx(20)


def test_insert_point_before_first():
    builder = TrackBuilder(make_track_metadata(40.0))
    
    points = [
            TrackPoint(10, 20, 50),
            TrackPoint(20, 30, 10),
            TrackPoint(30, 40, 30),
        ]
    
    builder._insert_point_at_distance(points, 0.0)

    assert [point.distance for point in points] == [0, 10, 20, 30]

    inserted = points[0]

    assert inserted.distance == pytest.approx(0.0)

    assert inserted.x == pytest.approx(30.0)
    assert inserted.z == pytest.approx(40.0)


def test_insert_point_after_last():
    builder = TrackBuilder(make_track_metadata(40.0))
    
    points = [
            TrackPoint(10, 20, 50),
            TrackPoint(20, 30, 10),
            TrackPoint(30, 40, 30),
        ]
    
    builder._insert_point_at_distance(points, 35.0)

    assert [point.distance for point in points] == [10, 20, 30, 35]

    inserted = points[-1]

    assert inserted.distance == pytest.approx(35.0)

    assert inserted.x == pytest.approx(35.0)
    assert inserted.z == pytest.approx(35.0)


def test_insert_point_track_length():
    builder = TrackBuilder(make_track_metadata(40.0))
    
    points = [
            TrackPoint(10, 20, 50),
            TrackPoint(20, 30, 10),
            TrackPoint(30, 40, 30),
        ]
    
    builder._insert_point_at_distance(points, 40.0)

    # distance should get set to 0
    assert [point.distance for point in points] == [0, 10, 20, 30]

    # now at pos 0 because dist set to 0
    inserted = points[0]

    assert inserted.distance == pytest.approx(0.0)

    assert inserted.x == pytest.approx(30.0)
    assert inserted.z == pytest.approx(40.0)

def test_finalise_inserts_boundaries():
    # bins appear every 5m, so sec3, marshal 2 and 3 should all not be in
    metadata = TrackMetadata(
        track_id=7,
        track_length=500,
        sector_2_start=150.0,
        sector_3_start=302.0,
        marshal_zone_starts=(75.0, 224.0, 403.0)
    )

    builder = TrackBuilder(metadata)

    # add coverage bins
    add_car_coverage(
        builder,
        num_bins=100,
        num_cars=10,
    )

    geometry = builder.finalise()

    distances = [point.distance for point in geometry.points]

    for boundary in (75.0, 150.0, 224.0, 302.0, 403.0):
        # dont need both but just for explicitnes
        assert boundary in distances
        assert distances.count(boundary) == 1

    # also check correct x/z
    # values are not 302.0 due to interpolation of bin values (which are median of bins) and points stored at bin + 1m (e..g 301m)
    boundary_point = next(point for point in geometry.points if point.distance == 302.0)
    assert boundary_point.x == pytest.approx(300.5)
    assert boundary_point.z == pytest.approx(300.5)