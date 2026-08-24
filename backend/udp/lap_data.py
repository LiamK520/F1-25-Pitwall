from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader
from udp.constants import NUM_CARS

"""
//-----------------------------------------------------------------------------
// Lap - 1285 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Lap data about one car
//-----------------------------------------------------------------------------
struct LapData
{
    uint32      m_lastLapTimeInMS;              // Last lap time in milliseconds
    uint32      m_currentLapTimeInMS;           // Current time around the lap in milliseconds
    uint16      m_sector1TimeMSPart;            // Sector 1 time milliseconds part
    uint8       m_sector1TimeMinutesPart;       // Sector 1 whole minute part
    uint16      m_sector2TimeMSPart;            // Sector 2 time milliseconds part
    uint8       m_sector2TimeMinutesPart;       // Sector 2 whole minute part
    uint16      m_deltaToCarInFrontMSPart;      // Time delta to car in front milliseconds part
    uint8       m_deltaToCarInFrontMinutesPart; // Time delta to car in front whole minute part
    uint16      m_deltaToRaceLeaderMSPart;      // Time delta to race leader milliseconds part
    uint8       m_deltaToRaceLeaderMinutesPart; // Time delta to race leader whole minute part
    float       m_lapDistance;                  // Distance vehicle is around current lap in metres – could be negative if line hasn’t been crossed yet
    float       m_totalDistance;                // Total distance travelled in session in metres – could be negative if line hasn’t been crossed yet
    float       m_safetyCarDelta;               // Delta in seconds for safety car
    uint8       m_carPosition;                  // Car race position
    uint8       m_currentLapNum;                // Current lap number
    uint8       m_pitStatus;                    // 0 = none, 1 = pitting, 2 = in pit area
    uint8       m_numPitStops;                  // Number of pit stops taken in this race
    uint8       m_sector;                       // 0 = sector1, 1 = sector2, 2 = sector3
    uint8       m_currentLapInvalid;            // Current lap invalid - 0 = valid, 1 = invalid
    uint8       m_penalties;                    // Accumulated time penalties in seconds to be added
    uint8       m_totalWarnings;                // Accumulated number of warnings issued
    uint8       m_cornerCuttingWarnings;        // Accumulated number of corner cutting warnings issued
    uint8       m_numUnservedDriveThroughPens;  // Num drive through pens left to serve
    uint8       m_numUnservedStopGoPens;        // Num stop go pens left to serve
    uint8       m_gridPosition;                 // Grid position the vehicle started the race in
    uint8       m_driverStatus;                 // Status of driver - 0 = in garage, 1 = flying lap, 2 = in lap, 3 = out lap, 4 = on track
    uint8       m_resultStatus;                 // Result status - 0 = invalid, 1 = inactive, 2 = active, 3 = finished, 4 = didnotfinish, 5 = disqualified, 6 = not classified, 7 = retired
    uint8       m_pitLaneTimerActive;           // Pit lane timing, 0 = inactive, 1 = active
    uint16      m_pitLaneTimeInLaneInMS;        // If active, the current time spent in the pit lane in ms
    uint16      m_pitStopTimerInMS;             // Time of the actual pit stop in ms
    uint8       m_pitStopShouldServePen;        // Whether the car should serve a penalty at this stop
    float       m_speedTrapFastestSpeed;        // Fastest speed through speed trap for this car in kmph
    uint8       m_speedTrapFastestLap;          // Lap no the fastest speed was achieved, 255 = not set
};

struct PacketLapData
{
    PacketHeader    m_header;               // Header

    // Packet specific data
    LapData     m_lapData[cs_maxNumCarsInUDPData];      // Lap data for all cars on track

    uint8       m_timeTrialPBCarIdx;                    // Index of Personal Best car in time trial (255 if invalid)
    uint8       m_timeTrialRivalCarIdx;                 // Index of Rival car in time trial (255 if invalid)
};

"""

LAP_DATA_STRUCT = struct.Struct(
    "<"
    "II"        # last lap time, current lap time
    "HB"        # sector 1 ms part, minutes part
    "HB"        # sector 2 ms part, minutes part
    "HB"        # delta to car in front ms part, minutes part
    "HB"        # delta to race leader ms part, minutes part
    "fff"       # lap distance, total distance, safety car delta
    "15B"       # race/lap/pit/status fields
    "HH"        # pit lane time, pit stop time
    "B"         # serve penalty at pit stop
    "f"         # fastest speed trap speed
    "B"         # lap fastest speed trap was achieved
)

LAP_DATA_SIZE = LAP_DATA_STRUCT.size

LAP_DATA_PACKET_SIZE = 1285


@dataclass(frozen=True)
class LapData:
    last_lap_time_ms: int
    current_lap_time_ms: int

    sector1_time_ms_part: int
    sector1_time_minutes_part: int
    sector2_time_ms_part: int
    sector2_time_minutes_part: int

    delta_to_car_in_front_ms_part: int
    delta_to_car_in_front_minutes_part: int
    delta_to_race_leader_ms_part: int
    delta_to_race_leader_minutes_part: int

    lap_distance: float
    total_distance: float
    safety_car_delta: float

    car_position: int
    current_lap_num: int
    pit_status: int
    num_pit_stops: int
    sector: int
    current_lap_invalid: int
    penalties: int
    total_warnings: int
    corner_cutting_warnings: int
    num_unserved_drive_through_pens: int
    num_unserved_stop_and_go_pens: int
    grid_position: int
    driver_status: int
    result_status: int
    pit_lane_timer_active: int

    pit_lane_time_in_lane_ms: int
    pit_stop_timer_ms: int
    pit_stop_should_serve_pen: int

    speed_trap_fastest_speed: float
    speed_trap_fastest_lap: int

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "LapData":
        values = LAP_DATA_STRUCT.unpack_from(data, offset)

        return cls(*values)


@dataclass(frozen=True)
class LapDataPacket:
    header: PacketHeader
    cars: tuple[LapData, ...]

    time_trial_pb_car_index: int
    time_trial_rival_car_index: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "LapDataPacket":
        if len(data) != LAP_DATA_PACKET_SIZE:
            raise ValueError(
                f"Error: Invalid LapData packet size. Expected {LAP_DATA_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        offset = HEADER_SIZE
        cars = []

        for _ in range(NUM_CARS):
            lap_data = LapData.from_bytes(data, offset)
            cars.append(lap_data)
            offset += LAP_DATA_SIZE

        time_trial_pb_car_index = data[offset]
        time_trial_rival_car_index = data[offset + 1]

        return cls(
            header=header,
            cars=tuple(cars),
            time_trial_pb_car_index=time_trial_pb_car_index,
            time_trial_rival_car_index=time_trial_rival_car_index
        )