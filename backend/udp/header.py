from dataclasses import dataclass
import struct

# udp telemetry details: https://forums.ea.com/discussions/f1-25-general-discussion-en/discussion-f1%C2%AE-25-udp-specification/12187351
"""
// Different packet types
enum PacketId
{
    ePacketIdMotion                 = 0,    // Contains all motion data for player’s car – only sent while player is in control
    ePacketIdSession                = 1,    // Data about the session – track, time left
    ePacketIdLapData                = 2,    // Data about all the lap times of cars in the session
    ePacketIdEvent                  = 3,    // Various notable events that happen during a session
    ePacketIdParticipants           = 4,    // List of participants in the session, mostly relevant for multiplayer
    ePacketIdCarSetups              = 5,    // Packet detailing car setups for cars in the race
    ePacketIdCarTelemetry           = 6,    // Telemetry data for all cars
    ePacketIdCarStatus              = 7,    // Status data for all cars
    ePacketIdFinalClassification    = 8,    // Final classification confirmation at the end of a race
    ePacketIdLobbyInfo              = 9,    // Information about players in a multiplayer lobby
    ePacketIdCarDamage              = 10,   // Damage status for all cars
    ePacketIdSessionHistory         = 11,   // Lap and tyre data for session
    ePacketIdTyreSets               = 12,   // Extended tyre set data
    ePacketIdMotionEx               = 13,   // Extended motion data for player car
    ePacketIdTimeTrial              = 14,   // Time Trial specific data
    ePacketIdLapPositions           = 15,   // Lap positions on each lap so a chart can be constructed
    ePacketIdMax
};

struct PacketHeader
{
    uint16      m_packetFormat;             // 2025
    uint8       m_gameYear;                 // Game year - last two digits e.g. 25
    uint8       m_gameMajorVersion;         // Game major version - "X.00"
    uint8       m_gameMinorVersion;         // Game minor version - "1.XX"
    uint8       m_packetVersion;            // Version of this packet type
    uint8       m_packetId;                 // Identifier for the packet type
    uint64      m_sessionUID;               // Unique identifier for the session
    float       m_sessionTime;              // Session timestamp
    uint32      m_frameIdentifier;          // Identifier for the frame the data was retrieved on
    uint32      m_overallFrameIdentifier;   // Overall identifier for the frame the data was retrieved on, doesn't go back after flashbacks
    uint8       m_playerCarIndex;           // Index of player's car in the array
    uint8       m_secondaryPlayerCarIndex;  // Index of secondary player's car in the array (splitscreen) - 255 if no second player
};
"""

HEADER_SIZE = 29
# little endian encoding of above packet header types
# define this here instead of in unpack as we will likely be unpacking many times per second
HEADER_STRUCT = struct.Struct("<HBBBBBQfIIBB")

# frozen dataclass as we do not want to change a packet header once we receive it
@dataclass(frozen = True)
class PacketHeader:
    packet_format: int
    game_year: int
    game_major_version: int
    game_minor_version: int
    packet_version: int
    packet_id: int
    session_uid: int
    session_time: float
    frame_identifier: int
    overall_frame_identifier: int
    player_car_index: int
    secondary_player_car_index: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "PacketHeader":
        if len(data) < HEADER_SIZE:
            raise ValueError(
                f"Error: Packet too short for header: expected at least {HEADER_SIZE} bytes but got {len(data)}"
            )

        values = HEADER_STRUCT.unpack_from(data)

        return cls(*values)