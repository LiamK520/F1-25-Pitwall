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

    def finish(
        self,
        lap_time_ms: int | None,
        valid: bool,
    ) -> "LapTelemetry":
        """
        Converts the buffer into a fixed LapTelemetry dataclass.
        """

        return LapTelemetry(
            lap_number=self.lap_number,
            lap_time_ms=lap_time_ms,
            valid=valid,

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

# fixed dataclass that uses numpy arrays to store data more compactly and allow for easier data analysis in future
@dataclass(frozen=True)
class LapTelemetry:
    """
    Stores completed telemetry history for one lap.
    """

    lap_number: int

    lap_time_ms: int | None
    valid: bool

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