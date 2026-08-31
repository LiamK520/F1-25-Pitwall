from dataclasses import dataclass


@dataclass(frozen=True)
class TrackPoint:
    """
    Represents an actual point on the track
    """

    distance: float
    x: float
    z: float


@dataclass(frozen=True)
class TrackMetadata:
    track_id: int
    track_length: int

    sector_2_start: float
    sector_3_start: float
    marshal_zone_starts: tuple[float,...]


@dataclass(frozen=True)
class TrackGeometry:
    """
    final representation of the current track
    """

    # metadata
    track_id: int
    track_length: int

    min_x: float
    min_z: float
    max_x: float
    max_z: float

    sector_2_start: float
    sector_3_start: float

    # this should allow for dynamic highlgting of flags on final map hopefully
    marshal_zone_starts: tuple[float, ...]

    # track ddata
    points: tuple[TrackPoint, ...]
