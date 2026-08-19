from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader
from udp.constants import NUM_CARS


"""
//-----------------------------------------------------------------------------
// Car Setups - 1133 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Data about one car setup
//-----------------------------------------------------------------------------
struct CarSetupData
{
    uint8       m_frontWing;                // Front wing aero
    uint8       m_rearWing;                 // Rear wing aero
    uint8       m_onThrottle;               // Differential adjustment on throttle (percentage)
    uint8       m_offThrottle;              // Differential adjustment off throttle (percentage)
    float       m_frontCamber;              // Front camber angle (suspension geometry)
    float       m_rearCamber;               // Rear camber angle (suspension geometry)
    float       m_frontToe;                 // Front toe angle (suspension geometry)
    float       m_rearToe;                  // Rear toe angle (suspension geometry)
    uint8       m_frontSuspension;          // Front suspension
    uint8       m_rearSuspension;           // Rear suspension
    uint8       m_frontAntiRollBar;         // Front anti-roll bar
    uint8       m_rearAntiRollBar;          // Front anti-roll bar
    uint8       m_frontSuspensionHeight;    // Front ride height
    uint8       m_rearSuspensionHeight;     // Rear ride height
    uint8       m_brakePressure;            // Brake pressure (percentage)
    uint8       m_brakeBias;                // Brake bias (percentage)
    uint8       m_engineBraking;            // Engine braking (percentage)
    float       m_rearLeftTyrePressure;     // Rear left tyre pressure (PSI)
    float       m_rearRightTyrePressure;    // Rear right tyre pressure (PSI)
    float       m_frontLeftTyrePressure;    // Front left tyre pressure (PSI)
    float       m_frontRightTyrePressure;   // Front right tyre pressure (PSI)
    uint8       m_ballast;                  // Ballast
    float       m_fuelLoad;                 // Fuel load
};

struct PacketCarSetupData
{
    PacketHeader    m_header;               // Header

    // Packet specific data
    CarSetupData    m_carSetupData[cs_maxNumCarsInUDPData];

    float           m_nextFrontWingValue;   // Value of front wing after next pit stop - player only
};
"""

CAR_SETUP_STRUCT = struct.Struct(
    "<4B" # front wing to off throtle
    "4f" # camber toe
    "9B" # sus to engine braking
    "4f" # pressure
    "Bf" # ballast and load
)

CAR_SETUP_STRUCT_SIZE = CAR_SETUP_STRUCT.size

CAR_SETUP_PACKET_SIZE = 1133


@dataclass(frozen=True)
class CarSetupData:
    front_wing: int
    rear_wing: int

    on_throttle: int
    off_throttle: int

    front_camber: float
    rear_camber: float
    front_toe: float
    rear_toe: float

    front_suspension: int
    rear_suspension: int
    front_anti_roll_bar: int
    rear_anti_roll_bar: int
    front_suspension_height: int
    rear_suspension_height: int

    brake_pressure: int
    brake_bias: int
    engine_braking: int

    rear_left_tyre_pressure: float
    rear_right_tyre_pressure: float
    front_left_tyre_pressure: float
    front_right_tyre_pressure: float

    ballast: int
    fuel_load: float


    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "CarSetupData":
        values = CAR_SETUP_STRUCT.unpack_from(data, offset)

        return cls(*values)


@dataclass(frozen=True)
class CarSetupPacket:
    header: PacketHeader

    car_setup_data: tuple[CarSetupData, ...]

    next_front_wing_value: float


    @classmethod
    def from_bytes(cls, data: bytes) -> "CarSetupPacket":
        if len(data) != CAR_SETUP_PACKET_SIZE:
            raise ValueError(
                f"Error: wrong packet size for CarSetupPacket. expected {CAR_SETUP_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        offset = HEADER_SIZE

        setups = []

        for _ in range(NUM_CARS):
            setup = CarSetupData.from_bytes(data, offset)
            setups.append(setup)
            offset += CAR_SETUP_STRUCT_SIZE

        car_setup_data = tuple(setups)

        next_front_wing_value = struct.unpack_from("<f", data, offset)[0]

        return cls(header, car_setup_data, next_front_wing_value)