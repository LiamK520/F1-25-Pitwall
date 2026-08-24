from dataclasses import dataclass

from udp.car_telemetry import CarTelemetryPacket
from udp.lap_data import LapDataPacket

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