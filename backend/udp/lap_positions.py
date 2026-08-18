from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader

from udp.constants import NUM_CARS

"""
//-----------------------------------------------------------------------------
// Lap Positions - 1131 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Packet to send UDP data about the lap positions in a session. It details
// the positions of all the drivers at the start of each lap
//-----------------------------------------------------------------------------
static const NEuint     cs_maxNumLapsInLapPositionsHistoryPacket = 50;

struct PacketLapPositionsData
{
    PacketHeader    m_header;                   // Header

    // Packet specific data
    uint8           m_numLaps;                  // Number of laps in the data
    uint8           m_lapStart;                 // Index of the lap where the data starts, 0 indexed

    // Array holding the position of the car in a given lap, 0 if no record
    uint8           m_positionForVehicleIdx[cs_maxNumLapsInLapPositionsHistoryPacket][cs_maxNumCarsInUDPData];
};
"""

MAX_NUM_LAPS_IN_LAP_POSITIONS_HISTORY_PACKET = 50

# number of uints in the 2d aray
_TOTAL_ARR_SIZE = MAX_NUM_LAPS_IN_LAP_POSITIONS_HISTORY_PACKET * NUM_CARS

LAP_POSITIONS_STRUCT = struct.Struct(
    "<BB" # first two fields
    # need + otherwise python multiplies first bit too
    + "B" * _TOTAL_ARR_SIZE # 2d arr
)

LAP_POSITIONS_PACKET_SIZE = 1131


@dataclass(frozen = True)
class LapPositionsPacket:
    header: PacketHeader

    num_laps: int
    lap_start: int

    position_for_vehicle_idx: tuple[tuple[int, ...], ...]


    @classmethod
    def from_bytes(cls, data: bytes):
        if len(data) != LAP_POSITIONS_PACKET_SIZE:
            raise ValueError(
                f"Error: wrong size for LapPositonPacket. expected {LAP_POSITIONS_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        values = LAP_POSITIONS_STRUCT.unpack_from(data, HEADER_SIZE)

        num_laps = values[0]
        lap_start = values[1]

        if num_laps > MAX_NUM_LAPS_IN_LAP_POSITIONS_HISTORY_PACKET:
            raise ValueError(
                f"error: num_laps ({num_laps}) exceeds maximum value ({MAX_NUM_LAPS_IN_LAP_POSITIONS_HISTORY_PACKET})"
            )

        offset = 2

        pos = []

        # only record num_laps as rest is useless
        for _ in range(num_laps):
            arr = values[offset:offset + NUM_CARS]
            pos.append(tuple(arr))
            offset += NUM_CARS

        return cls(header, num_laps, lap_start, position_for_vehicle_idx=tuple(pos))