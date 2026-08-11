from dataclasses import dataclass
import struct

from udp.constants import NUM_CARS
from udp.header import HEADER_SIZE, PacketHeader

"""
//-----------------------------------------------------------------------------
// Car Telemetry - 1352 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Telemetry data for one car
//-----------------------------------------------------------------------------
struct CarTelemetryData
{
    uint16      m_speed;                        // Speed of car in kilometres per hour
    float       m_throttle;                     // Amount of throttle applied (0.0 to 1.0)
    float       m_steer;                        // Steering (-1.0 (full lock left) to 1.0 (full lock right))
    float       m_brake;                        // Amount of brake applied (0.0 to 1.0)
    uint8       m_clutch;                       // Amount of clutch applied (0 to 100)
    int8        m_gear;                         // Gear selected (1-8, N=0, R=-1)
    uint16      m_engineRPM;                    // Engine RPM
    uint8       m_drs;                          // 0 = off, 1 = on
    uint8       m_revLightsPercent;             // Rev lights indicator (percentage)
    uint16      m_revLightsBitValue;            // Rev lights (bit 0 = leftmost LED, bit 14 = rightmost LED)
    uint16      m_brakesTemperature[4];         // Brakes temperature (celsius)
    uint8       m_tyresSurfaceTemperature[4];   // Tyres surface temperature (celsius)
    uint8       m_tyresInnerTemperature[4];     // Tyres inner temperature (celsius)
    uint16      m_engineTemperature;            // Engine temperature (celsius)
    float       m_tyresPressure[4];             // Tyre pressure (PSI)
    uint8       m_surfaceType[4];               // Driving surface, see appendices
};

struct PacketCarTelemetryData
{
    PacketHeader        m_header;               // Header

    // Packet specific data
    CarTelemetryData    m_carTelemetryData[cs_maxNumCarsInUDPData];   // data for all cars on track

    uint8               m_mfdPanelIndex;                // Index of MFD panel open - 255 = MFD closed
                                                        // Single player, race – 0 = Car setup, 1 = Pits
                                                        // 2 = Damage, 3 =  Engine, 4 = Temperatures
                                                        // May vary depending on game mode
    uint8               m_mfdPanelIndexSecondaryPlayer; // See above
    int8                m_suggestedGear;                // Suggested gear for the player (1-8), 0 if no gear suggested
};
"""

# binary structure just for telemetry struct, we can unpack the last few bits manually
CAR_TELEMETRY_STRUCT = struct.Struct(
    "<"
    "H"       # speed
    "fff"     # throttle, steer, brake
    "B"       # clutch
    "b"       # gear
    "H"       # engine RPM
    "BB"      # DRS, rev lights percent
    "H"       # rev lights bit value
    "4H"      # brake temperatures
    "4B"      # tyre surface temperatures
    "4B"      # tyre inner temperatures
    "H"       # engine temperature
    "4f"      # tyre pressures
    "4B"      # surface types
)

CAR_TELEMETRY_SIZE = CAR_TELEMETRY_STRUCT.size

CAR_TELEMETRY_PACKET_SIZE = 1352


@dataclass(frozen=True)
class CarTelemetryData:
    speed: int

    throttle: float
    steer: float
    brake: float

    clutch: int
    gear: int
    engine_rpm: int

    drs: int
    rev_lights_percent: int
    rev_lights_bit_value: int

    brakes_temperature: tuple[int,int,int,int]
    tyres_surface_temperature: tuple[int,int, int,int]
    tyres_inner_temperature: tuple[int,int,int,int]

    engine_temperature: int

    tyres_pressure: tuple[float,float, float, float]
    surface_type: tuple[int, int, int, int]


    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "CarTelemetryData":
        values = CAR_TELEMETRY_STRUCT.unpack_from(data, offset)

        return cls(
            speed=values[0],

            throttle=values[1],
            steer=values[2],
            brake=values[3],

            clutch=values[4],
            gear=values[5],
            engine_rpm=values[6],

            drs=values[7],
            rev_lights_percent=values[8],
            rev_lights_bit_value=values[9],

            brakes_temperature=tuple(values[10:14]),
            tyres_surface_temperature=tuple(values[14:18]),
            tyres_inner_temperature=tuple(values[18:22]),

            engine_temperature=values[22],

            tyres_pressure=tuple(values[23:27]),
            surface_type=tuple(values[27:31]),
        )


@dataclass(frozen=True)
class CarTelemetryPacket:
    header: PacketHeader
    cars: tuple[CarTelemetryData, ...]

    mfd_panel_index: int
    mfd_panel_index_secondary_player: int
    suggested_gear: int

    @classmethod
    def from_bytes(cls, data: bytes) -> "CarTelemetryPacket":
        if len(data) != CAR_TELEMETRY_PACKET_SIZE:
            raise ValueError(f"Error: Invalid CarTelemetry packet size. Expected {CAR_TELEMETRY_PACKET_SIZE} but got {len(data)}")

        header = PacketHeader.from_bytes(data)

        cars = []
        offset = HEADER_SIZE

        for _ in range(NUM_CARS):
            telem = CarTelemetryData.from_bytes(data, offset)
            cars.append(telem)
            offset += CAR_TELEMETRY_SIZE

        mfd_panel_index = data[offset]
        mfd_panel_index_secondary_player = data[offset + 1]

        # unpack is necessary as suggested gear is signed int
        suggested_gear = struct.unpack_from("<b", data, offset + 2,)[0]

        return cls(
            header=header,
            cars=tuple(cars),
            mfd_panel_index=mfd_panel_index,
            mfd_panel_index_secondary_player=mfd_panel_index_secondary_player,
            suggested_gear=suggested_gear,
        )