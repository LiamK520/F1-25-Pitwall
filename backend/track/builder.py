from dataclasses import dataclass

from udp.constants import NUM_CARS
from udp.lap_data import LapDataPacket
from udp.motion import MotionPacket

import math
from statistics import median

from track.geometry import TrackPoint, TrackMetadata, TrackGeometry


@dataclass(frozen=True)
class TrackSample:
    """
    Stores lap data and motion for the same frame, for a specific car.

    Used to construct map
    """

    # tracking car idx and lap num for now as will probably be useful for figuring out if our
    # track esimate is reliable (e.g. not dominated by one car which is susceptible to driver error etc.)
    car_index: int
    lap_number: int
    lap_distance: float

    x: float
    z: float


class TrackBuilder:

    # groups points into bins separated by 5m
    # this is probably fine for all tracks in the game, but maybe doing a fraction of track length could be better
    # especially for considering possible modded tracks (particularly ones of short length e.g. < 1km)
    BIN_SIZE = 5.0

    # targets for track saving
    # 99% of the track must be covered by at least 10 cars
    # 10 is chosen to allow good coverage of each bin, whilst also factoring in dnfs, pits etc. which are very unlikely to affect 10+ cars
    # note that a general coverage of 100% is also required
    MIN_FINALISE_CARS = 10
    MIN_FINALISE_CAR_COVERAGE = 0.99

    def __init__(self, metadata: TrackMetadata):
        self.samples: list[TrackSample] = []
        self.metadata = metadata

        # just for easiness to avoid refactor

        self.track_length = metadata.track_length


    def process_frame(self, lap_packet: LapDataPacket, motion_packet: MotionPacket):
        for i in range(NUM_CARS):
            lap = lap_packet.cars[i]
            motion = motion_packet.cars[i]

            # ignore prerace, pit and not running car
            if lap.current_lap_num <= 0 or lap.pit_status != 0 or lap.result_status != 2:
                continue

            self.samples.append(TrackSample(
                car_index=i,
                lap_number=lap.current_lap_num,
                lap_distance=lap.lap_distance,
                x=motion.world_position_x,
                z=motion.world_position_z
            ))

    def _build_bins(self) -> list[list[TrackSample]]:
        """
        groups samples into bins based on dist
        """

        num_bins = math.ceil(self.track_length / self.BIN_SIZE)

        bins = [[] for _ in range(num_bins)]

        for sample in self.samples:
            dist = sample.lap_distance

            # dont know if this can happen but to be safe skip
            if dist < 0 or dist > self.track_length:
                continue

            # bound to bins- 1 in case lap dist = track len
            index = min(int(dist // self.BIN_SIZE), num_bins - 1)
            bins[index].append(sample)

        return bins

    def build_points(self) -> list[TrackPoint | None]:
        """
        Returns a list of TrackPoints from the current recorded samples.

        The returned list may contain None, indicating no values recorded for that segment of track.
        """
        bins = self._build_bins()
        num_bins = len(bins)

        points = [None] * num_bins

        for i in range(num_bins):
            if not bins[i]:
                continue
            # make dist avg between this bin and next
            dist = min(i * self.BIN_SIZE + self.BIN_SIZE / 2, self.track_length)
            # get median for rest
            # median should hopefully be good enough to get rid of outliers (e.g. runoffs) see sure
            x = median([sample.x for sample in bins[i]])
            z = median([sample.z for sample in bins[i]])

            point = TrackPoint(dist, x, z)
            points[i] = point

        return points


    def coverage(self) -> float:
        """
        Returns the amount of track distance bins that contain enough data for a track point, as a fraction between 0 and 1
        """
        bins = self._build_bins()
        if not bins:
            return 0.0

        coverage = sum(bool(samples) for samples in bins)

        return coverage / len(bins)


    def sample_counts(self) -> list[int]:
        """
        returns number of samples in each bin
        """
        return [len(samples) for samples in self._build_bins()]


    def car_counts(self) -> list[int]:
        """
        returns number of unique cars with data points in each bin
        """

        # use set to get unique car id probably easiest
        return [len({sample.car_index for sample in samples}) for samples in self._build_bins()]


    def car_coverage(self, minimum_cars: int) -> float:
        counts = self.car_counts()

        if not counts:
            return 0.0

        reliability = sum(count >= minimum_cars for count in counts)

        return reliability / len(counts)


    def ready_to_finalise(self) -> bool:
        """
        determines if the track is ready to be saved based on the coverage 
        """
        return self.coverage() >= 1.0 and self.car_coverage(self.MIN_FINALISE_CARS) >= self.MIN_FINALISE_CAR_COVERAGE


    def _interpolate_point(self, before: TrackPoint, after: TrackPoint, distance: float) -> TrackPoint:
        """
        Creates a track point between before and after, at distance by interpolating
        """
        # get scale factor for the x and z stuff
        scale = (distance - before.distance) / (after.distance - before.distance)

        # scaling formula
        # scale = target - before / after - before
        # scale(after - before) + before = target

        new_x = before.x + scale * (after.x - before.x)
        new_z = before.z + scale * (after.z - before.z)

        return TrackPoint(distance, new_x, new_z)


    def _interpolate_wraparound_point(self, before: TrackPoint, after:TrackPoint, distance: float) -> TrackPoint:
        """
        Creates a trackpoint where before and after crosses the start/finish line
        """

        # interpolating between final and first point, where distance is before first point distance
        if distance < before.distance and distance < after.distance:
            # easiest way to handle this is probably just make before a negative distance
            new_point = TrackPoint(before.distance - self.track_length, before.x, before.z)

            # now interpolate as normal
            return self._interpolate_point(new_point, after, distance)

        # interpolating between final and first point, where distance is after final point distance
        if distance > before.distance and distance > after.distance:
            new_point = TrackPoint(after.distance + self.track_length, after.x, after.z)

            return self._interpolate_point(before, new_point, distance)

        # something weird with the points is going on if neither case hits
        raise RuntimeError("Incorrect point setup for a wraparound interpolation")


    def _insert_point_at_distance(self, points: list[TrackPoint], distance: float) -> None:
        """
        Insert a trackponit at the desired distance in the points list
        """

        # even tho prerace we can have negative distance, raise error anyway
        # interpolation at negative distance should never happen
        if distance < 0 or distance > self.track_length:
            raise ValueError(f"Outside track bounds: attempted to add dist {distance}m on track of length {self.track_length}m")

        # should be same thing. making it 0 avoids having different values for the same idea (star/finish line)
        if distance == self.track_length:
            distance = 0

        # linear search should be fine but if not come back to this and make it binary search or interpolation serach
       
        if distance < points[0].distance:
            point = self._interpolate_wraparound_point(points[-1], points[0], distance)
            points.insert(0, point)
            return

        if distance == points[0].distance:
            return
        
        for i in range(1, len(points)):
            if distance == points[i].distance:
                # nothing to be done
                return

            if distance < points[i].distance:
                point = self._interpolate_point(points[i - 1], points[i], distance)
                points.insert(i, point)
                return

        if distance == points[-1].distance:
            return

        # otherwise we must be past final point
        point = self._interpolate_wraparound_point(points[-1], points[0], distance)
        points.append(point)
        return


    def finalise(self) -> TrackGeometry:
        """
        build the final represnetation of the current track.

        must contain enough data to finalise, see ready_to_finalise

        raises `RuntimeError` if ready_to_finalise is false
        """

        if not self.ready_to_finalise():
            raise RuntimeError("TrackBuilder: cannot finalise track geometry before sufficient data is collected")

        built_points = self.build_points()

        boundaries = [0.0, self.metadata.sector_2_start, self.metadata.sector_3_start, *self.metadata.marshal_zone_starts]

        # every bin contains a point but just to be sure filter
        points = [point for point in built_points if point is not None]

        # inserts points at marshall zone and sector starts
        # this is important as when the frontend renders map, having points at these areas should allow for dynamic highlighting
        # like yellow flags in martial zones, or just colouring different sectors different colours
        for dist in boundaries:
            self._insert_point_at_distance(points, dist)



        min_x = min(point.x for point in points)
        max_x = max(point.x for point in points)
        min_z = min(point.z for point in points)
        max_z = max(point.z for point in points)

        return TrackGeometry(
            track_id=self.metadata.track_id,
            track_length=self.metadata.track_length,

            min_x=min_x,
            max_x=max_x,
            min_z=min_z,
            max_z=max_z,

            sector_2_start=self.metadata.sector_2_start,
            sector_3_start=self.metadata.sector_3_start,

            marshal_zone_starts=self.metadata.marshal_zone_starts,

            points=tuple(points),
        )