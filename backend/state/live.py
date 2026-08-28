from dataclasses import dataclass

from udp.car_telemetry import CarTelemetryPacket
from udp.lap_data import LapDataPacket
from udp.motion import MotionPacket

@dataclass
class FramePackets:
    """
    Contains lap data, telemetry and motion data for the same frame.

    Some uses of this class may only rely on a few of these packets
    """

    lap_data: LapDataPacket | None = None
    telemetry: CarTelemetryPacket | None = None
    motion: MotionPacket | None = None

    # prevents the same frame being processed more than once
    live_processed: bool = False

    track_processed: bool = False


@dataclass(frozen=True)
class MatchedLiveFrame:
    lap_data: LapDataPacket
    telemetry: CarTelemetryPacket

    @property
    def overall_frame_identifier(self) -> int:
        return self.lap_data.header.overall_frame_identifier

    @property
    def session_time(self) -> float:
        return self.lap_data.header.session_time