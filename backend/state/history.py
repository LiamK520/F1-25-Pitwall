from dataclasses import dataclass, field

import numpy as np


# simple dataclass for easily appending new samples using pytohn lists
@dataclass
class LapTelemetryBuffer:
    """
    Buffer for telemetry data whilst a lap is in progress. 
    When the lap is completed, the data is converted to a LapTelemetry object that stores the samples in np arrays
    """

    lap_number: int
    # used to check if a lap is fully complete. true if lap was started after a transition e.g. 3->4
    started_at_lap_boundary: bool = False

    session_time: list[float] = field(default_factory=list)
    lap_distance: list[float] = field(default_factory=list)

    speed: list[int] = field(default_factory=list)
    throttle: list[float] = field(default_factory=list)
    brake: list[float] = field(default_factory=list)
    steer: list[float] = field(default_factory=list)

    gear: list[int] = field(default_factory=list)
    engine_rpm: list[int] = field(default_factory=list)

    drs: list[bool] = field(default_factory=list)

    def append(
        self, 
        session_time: float,
        lap_distance: float,
        speed: int,
        throttle: float,
        brake: float,
        steer: float,
        gear: int,
        engine_rpm: int,
        drs: bool,
    ) -> None:
        """Log a telemetry sample to the current lap"""

        self.session_time.append(session_time)
        self.lap_distance.append(lap_distance)

        self.speed.append(speed)
        self.throttle.append(throttle)
        self.brake.append(brake)
        self.steer.append(steer)

        self.gear.append(gear)
        self.engine_rpm.append(engine_rpm)

        self.drs.append(drs)

    def finish(self) -> "LapTelemetry":
        """
        Converts the buffer into a fixed LapTelemetry dataclass.
        """

        return LapTelemetry(
            lap_number=self.lap_number,

            session_time=np.asarray(
                self.session_time,
                dtype=np.float32,
            ),

            lap_distance=np.asarray(
                self.lap_distance,
                dtype=np.float32,
            ),

            speed=np.asarray(
                self.speed,
                dtype=np.uint16,
            ),

            throttle=np.asarray(
                self.throttle,
                dtype=np.float32,
            ),

            brake=np.asarray(
                self.brake,
                dtype=np.float32,
            ),

            steer=np.asarray(
                self.steer,
                dtype=np.float32,
            ),

            gear=np.asarray(
                self.gear,
                dtype=np.int8,
            ),

            engine_rpm=np.asarray(
                self.engine_rpm,
                dtype=np.uint16,
            ),

            drs=np.asarray(
                self.drs,
                dtype=np.bool_,
            ),
        )

    def trim_after_session_time(self, flashback_time: float) -> None:
        """
        Remove telemetry samples recorded after the specified time.

        All telemetry samples remain algined.
        """
        keep = [i for i, t in enumerate(self.session_time) if t <= flashback_time]

        # slightly inefficient but should be fine given frequency of flashbacks and relatively small data sizes
        self.session_time = [self.session_time[i] for i in keep]
        self.lap_distance = [self.lap_distance[i] for i in keep]
        self.brake = [self.brake[i] for i in keep]
        self.speed = [self.speed[i] for i in keep]
        self.throttle = [self.throttle[i] for i in keep]
        self.steer = [self.steer[i] for i in keep]
        self.gear = [self.gear[i] for i in keep]
        self.engine_rpm = [self.engine_rpm[i] for i in keep]
        self.drs = [self.drs[i] for i in keep]

# fixed dataclass that uses numpy arrays to store data more compactly and allow for easier data analysis in future
@dataclass(frozen=True)
class LapTelemetry:
    """
    Stores completed telemetry history for one lap.
    """

    lap_number: int

    session_time: np.ndarray
    lap_distance: np.ndarray

    speed: np.ndarray
    throttle: np.ndarray
    brake: np.ndarray
    steer: np.ndarray

    gear: np.ndarray
    engine_rpm: np.ndarray

    drs: np.ndarray

    @property
    def num_samples(self) -> int:
        """Return the number of telemetry samples stored for the lap."""

        return len(self.lap_distance)

    # converting back to buffer may be needed in case of flashback crossing laps
    def to_buffer(self) -> LapTelemetryBuffer:
        """
        Converts the current LapTelemetry to a LapTelemetryBuffer.

        This should mainly be used for handling flashbacks that cross a lap.
        """
        # can always assume started at boundary as shouldn't be in a completed lap telem otherwise
        buffer = LapTelemetryBuffer(self.lap_number, started_at_lap_boundary=True)

        buffer.session_time = self.session_time.tolist()
        buffer.lap_distance = self.lap_distance.tolist()
        buffer.speed = self.speed.tolist()
        buffer.throttle = self.throttle.tolist()
        buffer.brake = self.brake.tolist()
        buffer.steer = self.steer.tolist()
        buffer.gear = self.gear.tolist()
        buffer.engine_rpm = self.engine_rpm.tolist()
        buffer.drs = self.drs.tolist()

        return buffer