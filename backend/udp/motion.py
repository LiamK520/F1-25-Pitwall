from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader

"""
static const uint32     cs_maxNumCarsInUDPData = 22;

//-----------------------------------------------------------------------------
// Motion - 1349 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Motion data for one car
//-----------------------------------------------------------------------------
struct CarMotionData
{
    float       m_worldPositionX;           // World space X position - metres
    float       m_worldPositionY;           // World space Y position
    float       m_worldPositionZ;           // World space Z position
    float       m_worldVelocityX;           // Velocity in world space X - metres/s
    float       m_worldVelocityY;           // Velocity in world space Y
    float       m_worldVelocityZ;           // Velocity in world space Z
    int16       m_worldForwardDirX;         // World space forward X direction (normalised)
    int16       m_worldForwardDirY;         // World space forward Y direction (normalised)
    int16       m_worldForwardDirZ;         // World space forward Z direction (normalised)
    int16       m_worldRightDirX;           // World space right X direction (normalised)
    int16       m_worldRightDirY;           // World space right Y direction (normalised)
    int16       m_worldRightDirZ;           // World space right Z direction (normalised)
    float       m_gForceLateral;            // Lateral G-Force component
    float       m_gForceLongitudinal;       // Longitudinal G-Force component
    float       m_gForceVertical;           // Vertical G-Force component
    float       m_yaw;                      // Yaw angle in radians
    float       m_pitch;                    // Pitch angle in radians
    float       m_roll;                     // Roll angle in radians
};

struct PacketMotionData
{
    PacketHeader    m_header;               // Header

    // Packet specific data
    CarMotionData   m_carMotionData[cs_maxNumCarsInUDPData];  // Data for all cars on track
};
"""

NUM_CARS = 22

CAR_MOTION_STRUCT = struct.Struct(
    "<"
    "ffffff"   # world position + velocity
    "hhhhhh"   # forward direction + right direction
    "ffffff"   # G-forces + yaw/pitch/roll
)

CAR_MOTION_SIZE = CAR_MOTION_STRUCT.size
MOTION_PACKET_SIZE = 1349

@dataclass(frozen=True)
class CarMotionData:
    world_position_x: float
    world_position_y: float
    world_position_z: float

    world_velocity_x: float
    world_velocity_y: float
    world_velocity_z: float

    world_forward_dir_x: int
    world_forward_dir_y: int
    world_forward_dir_z: int

    world_right_dir_x: int
    world_right_dir_y: int
    world_right_dir_z: int

    g_force_lateral: float
    g_force_longitudinal: float
    g_force_vertical: float

    yaw: float
    pitch: float
    roll: float

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "CarMotionData":
        # note we need offset here as we will be unpacking multiple cars later from the same bytes
        values = CAR_MOTION_STRUCT.unpack_from(data, offset)
        return cls(*values)

@dataclass(frozen=True)
class MotionPacket:
    header: PacketHeader
    cars: tuple[CarMotionData, ...]

    @classmethod
    def from_bytes(cls, data: bytes):
        if len(data) != MOTION_PACKET_SIZE:
            raise ValueError(
                f"Error: Invalid motion packet size. Expected {MOTION_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        cars = []
        offset = HEADER_SIZE

        # load motion data for all cars
        for _ in range(NUM_CARS):
            car = CarMotionData.from_bytes(data, offset)
            cars.append(car)
            offset += CAR_MOTION_SIZE

        return cls(
            header=header,
            cars=tuple(cars)
        )