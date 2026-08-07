from enum import IntEnum

from udp.header import PacketHeader
from udp.motion import MotionPacket
from udp.participants import ParticipantsPacket

"""
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
"""

class PacketId(IntEnum):
    MOTION = 0
    SESSION = 1
    LAP_DATA = 2
    EVENT = 3
    PARTICIPANTS = 4
    CAR_SETUPS = 5
    CAR_TELEMETRY = 6
    CAR_STATUS = 7
    FINAL_CLASSIFICATION = 8
    LOBBY_INFO = 9
    CAR_DAMAGE = 10
    SESSION_HISTORY = 11
    TYRE_SETS = 12
    MOTION_EX = 13
    TIME_TRIAL = 14
    LAP_POSITIONS = 15

def decode_packet(data: bytes):
    header = PacketHeader.from_bytes(data)

    try:
        packet_id = PacketId(header.packet_id)
    except ValueError:
        raise ValueError(f"Error: Unknown packet ID: {header.packet_id}")

    if packet_id == PacketId.MOTION:
        return MotionPacket.from_bytes(data)

    if packet_id == PacketId.PARTICIPANTS:
        return ParticipantsPacket.from_bytes(data)

    raise NotImplementedError(
        f"Packet type {packet_id.name} is not implemented yet"
    )