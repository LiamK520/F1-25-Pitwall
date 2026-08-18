from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader

"""
//-----------------------------------------------------------------------------
// Session History - 1460 bytes
//-----------------------------------------------------------------------------

static const uint     cs_maxNumLapsInHistory = 100;

struct LapHistoryData
{
    uint32      m_lapTimeInMS;              // Lap time in milliseconds
    uint16      m_sector1TimeMSPart;        // Sector 1 milliseconds part
    uint8       m_sector1TimeMinutesPart;   // Sector 1 whole minute part
    uint16      m_sector2TimeMSPart;        // Sector 2 time milliseconds part
    uint8       m_sector2TimeMinutesPart;   // Sector 2 whole minute part
    uint16      m_sector3TimeMSPart;        // Sector 3 time milliseconds part
    uint8       m_sector3TimeMinutesPart;   // Sector 3 whole minute part
    uint8       m_lapValidBitFlags;         // 0x01 bit set-lap valid,      0x02 bit set-sector 1 valid
                                            // 0x04 bit set-sector 2 valid, 0x08 bit set-sector 3 valid
};

struct TyreStintHistoryData
{
    uint8       m_endLap;               // Lap the tyre usage ends on (255 if current tyre)
    uint8       m_tyreActualCompound;   // Actual tyres used by this driver
    uint8       m_tyreVisualCompound;   // Visual tyres used by this driver
};

struct PacketSessionHistoryData
{
    PacketHeader    m_header;               // Header

    // Packet specific data
    uint8           m_carIdx;                   // Index of the car this lap data relates to
    uint8           m_numLaps;                  // Num laps in the data (including current partial lap)
    uint8           m_numTyreStints;            // Number of tyre stints in the data
    
    uint8           m_bestLapTimeLapNum;        // Lap the best lap time was achieved on
    uint8           m_bestSector1LapNum;        // Lap the best Sector 1 time was achieved on
    uint8           m_bestSector2LapNum;        // Lap the best Sector 2 time was achieved on
    uint8           m_bestSector3LapNum;        // Lap the best Sector 3 time was achieved on

    LapHistoryData          m_lapHistoryData[cs_maxNumLapsInHistory];   // 100 laps of data max
    TyreStintHistoryData    m_tyreStintsHistoryData[cs_maxTyreStints];
};
"""

MAX_LAPS_IN_HISTORY = 100
MAX_TYRE_STINTS = 8

LAP_HISTORY_STRUCT = struct.Struct(
    "<"
    "I"     # lap time
    "HB"    # sector 1
    "HB"    # sector 2
    "HB"    # sector 3
    "B"     # validity flags
)

LAP_HISTORY_SIZE = LAP_HISTORY_STRUCT.size


TYRE_STINT_HISTORY_STRUCT = struct.Struct("<BBB")

TYRE_STINT_HISTORY_SIZE = TYRE_STINT_HISTORY_STRUCT.size


SESSION_HISTORY_HEADER_STRUCT = struct.Struct("<7B")

SESSION_HISTORY_HEADER_SIZE = SESSION_HISTORY_HEADER_STRUCT.size


SESSION_HISTORY_PACKET_SIZE = 1460


@dataclass
class LapHistoryData:
    """
    Stores timing and validity of a single lap
    """

    lap_time_in_ms: int

    sector1_time_ms_part: int
    sector1_time_minutes_part: int

    sector2_time_ms_part: int
    sector2_time_minutes_part: int

    sector3_time_ms_part: int
    sector3_time_minutes_part: int

    lap_valid_bit_flags: int

    @classmethod
    def from_bytes(cls,data: bytes, offset: int) -> "LapHistoryData":

        values = LAP_HISTORY_STRUCT.unpack_from(data, offset)

        return cls(*values)


@dataclass(frozen=True)
class TyreStintHistoryData:
    """Stores infomration about a stint"""

    end_lap: int
    tyre_actual_compound: int
    tyre_visual_compound: int

    @classmethod
    def from_bytes(cls,data: bytes,offset: int) -> "TyreStintHistoryData":

        values = TYRE_STINT_HISTORY_STRUCT.unpack_from(data,offset)

        return cls(*values)


@dataclass(frozen=True)
class SessionHistoryPacket:
    """
    Stores lap and tyre-stint history for one vehicle.

    Only the first num_laps and num_tyre_stints entries in their respective
    arrays are considered valid.
    """

    header: PacketHeader

    car_idx: int

    num_laps: int
    num_tyre_stints: int

    best_lap_time_lap_num: int
    best_sector1_lap_num: int
    best_sector2_lap_num: int
    best_sector3_lap_num: int

    lap_history: tuple[LapHistoryData, ...]
    tyre_stints: tuple[TyreStintHistoryData, ...]

    @classmethod
    def from_bytes(cls, data: bytes) -> "SessionHistoryPacket":

        if len(data) != SESSION_HISTORY_PACKET_SIZE:
            raise ValueError(
                f"Invalid Session History packet size: expected {SESSION_HISTORY_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        # this is probably better way of unpacking things than done before, maybe change others
        (
            car_idx,
            num_laps,
            num_tyre_stints,
            best_lap_time_lap_num,
            best_sector1_lap_num,
            best_sector2_lap_num,
            best_sector3_lap_num,
        ) = SESSION_HISTORY_HEADER_STRUCT.unpack_from(data, HEADER_SIZE)

        if num_laps > MAX_LAPS_IN_HISTORY:
            raise ValueError(
                f"Invalid number of laps: {num_laps}"
            )

        if num_tyre_stints > MAX_TYRE_STINTS:
            raise ValueError(
                f"Invalid number of tyre stints: {num_tyre_stints}"
            )

        lap_history_offset = HEADER_SIZE + SESSION_HISTORY_HEADER_SIZE


        lap_history = tuple(
            LapHistoryData.from_bytes(data, lap_history_offset + i * LAP_HISTORY_SIZE)
            for i in range(num_laps)
        )

        tyre_stints_offset =lap_history_offset + MAX_LAPS_IN_HISTORY * LAP_HISTORY_SIZE

        tyre_stints = tuple(
            TyreStintHistoryData.from_bytes(data, tyre_stints_offset + i * TYRE_STINT_HISTORY_SIZE)
            for i in range(num_tyre_stints)
        )

        return cls(
            header=header,

            car_idx=car_idx,

            num_laps=num_laps,
            num_tyre_stints=num_tyre_stints,

            best_lap_time_lap_num=best_lap_time_lap_num,
            best_sector1_lap_num=best_sector1_lap_num,
            best_sector2_lap_num=best_sector2_lap_num,
            best_sector3_lap_num=best_sector3_lap_num,

            lap_history=lap_history,
            tyre_stints=tyre_stints,
        )