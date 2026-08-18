from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader

"""
//-----------------------------------------------------------------------------
// Tyre Sets - 231 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Data about one tyre set
//-----------------------------------------------------------------------------
struct TyreSetData
{
    uint8       m_actualTyreCompound;               // Actual tyre compound used
    uint8       m_visualTyreCompound;               // Visual tyre compound used
    uint8       m_wear;                             // Tyre wear (percentage)
    uint8       m_available;                        // Whether this set is currently available
    uint8       m_recommendedSession;               // Recommended session for tyre set, see appendix
    uint8       m_lifeSpan;                         // Laps left in this tyre set
    uint8       m_usableLife;                       // Max number of laps recommended for this compound
    int16       m_lapDeltaTime;                     // Lap delta time in milliseconds compared to fitted set
    uint8       m_fitted;                           // Whether the set is fitted or not
};

struct PacketTyreSetsData
{
    PacketHeader    m_header;                           // Header

    uint8           m_carIdx;                           // Index of the car this data relates to

    // Packet specific data
    TyreSetData     m_tyreSetData[cs_maxNumTyreSets];   // 13 (dry) + 7 (wet)

    uint8           m_fittedIdx;                        // Index into array of fitted tyre
};"""

NUM_TYRE_SETS = 20

TYRE_SET_STRUCT = struct.Struct(
    "<"
    "7B"
    "h"
    "B"
)

TYRE_SET_SIZE = TYRE_SET_STRUCT.size

TYRE_SETS_PACKET_SIZE = 231


@dataclass(frozen=True)
class TyreSetData:
    """Stores information about a unique set of tyres"""

    actual_tyre_compound: int
    visual_tyre_compound: int

    wear: int
    available: int

    recommended_session: int

    life_span: int
    usable_life: int

    lap_delta_time: int

    fitted: int

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "TyreSetData":

        values = TYRE_SET_STRUCT.unpack_from(data,  offset)

        return cls(*values)


@dataclass(frozen=True)
class TyreSetsPacket:
    """
    Stores tyre information for a car
    """

    header: PacketHeader

    car_idx: int

    tyre_sets: tuple[TyreSetData, ...]

    fitted_idx: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "TyreSetsPacket":
        if len(data) != TYRE_SETS_PACKET_SIZE:
            raise ValueError(
                f"Invalid Tyre Sets packet size: "
                f"expected {TYRE_SETS_PACKET_SIZE}, but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        car_idx = data[HEADER_SIZE]

        tyre_sets_offset = HEADER_SIZE + 1

        tyre_sets = tuple(
            TyreSetData.from_bytes(data,tyre_sets_offset + i * TYRE_SET_SIZE)
            for i in range(NUM_TYRE_SETS)
        )

        fitted_idx_offset = tyre_sets_offset + NUM_TYRE_SETS * TYRE_SET_SIZE

        fitted_idx = data[fitted_idx_offset]

        return cls(
            header=header,
            car_idx=car_idx,
            tyre_sets=tyre_sets,
            fitted_idx=fitted_idx,
        )