from dataclasses import dataclass

from udp.constants import NUM_CARS
from udp.lap_data import LapDataPacket
from udp.motion import MotionPacket

import math
from statistics import median


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


@dataclass(frozen=True)
class TrackPoint:
    """
    Represents an actual point on the track
    """

    distance: float
    x: float
    z: float


class TrackBuilder:

    # groups points into bins separated by 5m
    # this is probably fine for all tracks in the game, but maybe doing a fraction of track length could be better
    # especially for considering possible modded tracks (particularly ones of short length e.g. < 1km)
    BIN_SIZE = 5.0

    def __init__(self, track_length: int):
        self.samples: list[TrackSample] = []
        self.track_length = track_length


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


    def build_points(self) -> list[TrackPoint | None]:
        """
        Returns a list of TrackPoints from the current recorded samples.

        The returned list may contain None, indicating no values recorded for that segment of track.
        """
        num_bins = math.ceil(self.track_length / self.BIN_SIZE)

        bins = [[] for _ in range(num_bins)]

        for sample in self.samples:
            dist = sample.lap_distance

            # dont know if this can happen but to be safe skip
            if dist < 0:
                continue

            # bound to bins- 1 in case lap dist = track len
            index = min(int(dist // self.BIN_SIZE), num_bins - 1)
            bins[index].append(sample)

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
        points = self.build_points()

        if not points:
            return 0.0

        covered = sum(point is not None for point in points)

        return covered / len(points)