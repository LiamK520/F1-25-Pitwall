from dataclasses import dataclass
import struct

from udp.constants import NUM_CARS
from udp.header import HEADER_SIZE, PacketHeader

"""
//-----------------------------------------------------------------------------
// Final Classification - 1042 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Data about one participant's final results
//-----------------------------------------------------------------------------
struct FinalClassificationData
{
    uint8       m_position;                             // Finishing position
    uint8       m_numLaps;                              // Number of laps completed
    uint8       m_gridPosition;                         // Grid position of the car
    uint8       m_points;                               // Number of points scored
    uint8       m_numPitStops;                          // Number of pit stops made
    uint8       m_resultStatus;                         // Result status - 0 = invalid, 1 = inactive, 2 = active, 3 = finished, 4 = didnotfinish, 5 = disqualified, 6 = not classified, 7 = retired
    uint8       m_resultReason;                         // Result reason - 0 = invalid, 1 = retired, 2 = finished, 3 = terminal damage, 4 = inactive, 5 = not enough laps completed, 6 = black flagged
                                                        // 7 = red flagged, 8 = mechanical failure, 9 = session skipped, 10 = session simulated
    uint32      m_bestLapTimeInMS;                      // Best lap time of the session in milliseconds
    double      m_totalRaceTime;                        // Total race time in seconds without penalties
    uint8       m_penaltiesTime;                        // Total penalties accumulated in seconds
    uint8       m_numPenalties;                         // Number of penalties applied to this driver
    uint8       m_numTyreStints;                        // Number of tyres stints up to maximum
    uint8       m_tyreStintsActual[cs_maxTyreStints];   // Actual tyres used by this driver
    uint8       m_tyreStintsVisual[cs_maxTyreStints];   // Visual tyres used by this driver
    uint8       m_tyreStintsEndLaps[cs_maxTyreStints];  // The lap number stints end on
};

struct PacketFinalClassificationData
{
    PacketHeader    m_header;               // Header

    // Packet specific data
    uint8                       m_numCars;          // Number of cars in the final classification
    FinalClassificationData     m_classificationData[cs_maxNumCarsInUDPData];
};
"""

FINAL_CLASSIFICATION_STRUCT = struct.Struct(
    "<7B" # pos to reason
    "I" # best
    "d" # total race tim
    "3B" # rest of non array
    "24B" # array stuff
)

FINAL_CLASSIFICATION_SIZE = FINAL_CLASSIFICATION_STRUCT.size

MAX_TYRE_STINTS = 8 # from spec

FINAL_CLASSIFICATION_PACKET_SIZE = 1042


@dataclass(frozen=True)
class FinalClassificationData:
    """final classification of a single car"""

    position: int
    num_laps: int
    grid_position: int
    points: int
    num_pit_stops: int
    result_status: int
    result_reason: int

    best_lap_time_in_ms: int
    total_race_time: float
    penalties_time: int
    num_penalties: int
    num_tyre_stints: int

    tyre_stints_actual: tuple[int, ...]
    tyre_stints_visual: tuple[int, ...]
    tyre_stints_end_laps: tuple[int, ...]

    @classmethod
    def from_bytes(cls, data: bytes, offset: int):
        values = FINAL_CLASSIFICATION_STRUCT.unpack_from(data, offset)

        num_tyre_stints = values[11]

        if num_tyre_stints > MAX_TYRE_STINTS:
            raise ValueError(f"Invalid number of tyre stints: {num_tyre_stints}")

        tyre_stints_actual = tuple(values[12:20][:num_tyre_stints])

        tyre_stints_visual = tuple(values[20:28][:num_tyre_stints])

        tyre_stints_end_laps = tuple(values[28:36][:num_tyre_stints])

        return cls(
            position=values[0],
            num_laps=values[1],
            grid_position=values[2],

            points=values[3],
            num_pit_stops=values[4],

            result_status=values[5],
            result_reason=values[6],

            best_lap_time_in_ms=values[7],
            total_race_time=values[8],

            penalties_time=values[9],
            num_penalties=values[10],
            num_tyre_stints=num_tyre_stints,

            tyre_stints_actual=tyre_stints_actual,
            tyre_stints_visual=tyre_stints_visual,
            tyre_stints_end_laps=tyre_stints_end_laps,
        )

@dataclass(frozen=True)
class FinalClassificationPacket:
    """Stores final classificaiton of all cars"""

    header: PacketHeader

    num_cars: int

    classifications: tuple[FinalClassificationData, ...]

    @classmethod
    def from_bytes(cls, data: bytes):
        if len(data) != FINAL_CLASSIFICATION_PACKET_SIZE:
            raise ValueError(
                f"Error incorrect packet length for final classifcation. Expected {FINAL_CLASSIFICATION_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        offset = HEADER_SIZE + 1#

        num_cars = data[HEADER_SIZE]

        if num_cars > NUM_CARS:
            raise ValueError(f"Invalid number of cars: {num_cars}")

        cars = []

        for _ in range(num_cars):
            classification = FinalClassificationData.from_bytes(data, offset)
            cars.append(classification)
            offset += FINAL_CLASSIFICATION_SIZE

        return cls(
            header,
            num_cars,
            classifications=cars
        )