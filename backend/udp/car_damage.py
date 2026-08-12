from dataclasses import dataclass
import struct

from udp.constants import NUM_CARS
from udp.header import HEADER_SIZE, PacketHeader

"""
//-----------------------------------------------------------------------------
// Car Damage - 1041 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Car damage data for one car
//-----------------------------------------------------------------------------
struct CarDamageData
{
    float       m_tyresWear[4];                     // Tyre wear (percentage)
    uint8       m_tyresDamage[4];                   // Tyre damage (percentage)
    uint8       m_brakesDamage[4];                  // Brakes damage (percentage)
    uint8       m_tyreBlisters[4];                  // Tyre blisters value (percentage)
    uint8       m_frontLeftWingDamage;              // Front left wing damage (percentage)
    uint8       m_frontRightWingDamage;             // Front right wing damage (percentage)
    uint8       m_rearWingDamage;                   // Rear wing damage (percentage)
    uint8       m_floorDamage;                      // Floor damage (percentage)
    uint8       m_diffuserDamage;                   // Diffuser damage (percentage)
    uint8       m_sidepodDamage;                    // Sidepod damage (percentage)
    uint8       m_drsFault;                         // Indicator for DRS fault, 0 = OK, 1 = fault
    uint8       m_ersFault;                         // Indicator for ERS fault, 0 = OK, 1 = fault
    uint8       m_gearBoxDamage;                    // Gear box damage (percentage)
    uint8       m_engineDamage;                     // Engine damage (percentage)
    uint8       m_engineMGUHWear;                   // Engine wear MGU-H (percentage)
    uint8       m_engineESWear;                     // Engine wear ES (percentage)
    uint8       m_engineCEWear;                     // Engine wear CE (percentage)
    uint8       m_engineICEWear;                    // Engine wear ICE (percentage)
    uint8       m_engineMGUKWear;                   // Engine wear MGU-K (percentage)
    uint8       m_engineTCWear;                     // Engine wear TC (percentage)
    uint8       m_engineBlown;                      // Engine blown, 0 = OK, 1 = fault
    uint8       m_engineSeized;                     // Engine seized, 0 = OK, 1 = fault
};

struct PacketCarDamageData
{
    PacketHeader    m_header;               // Header

    // Packet specific data
    CarDamageData   m_carDamageData[cs_maxNumCarsInUDPData];      // data for all cars on track
};
"""

CAR_DAMAGE_STRUCT = struct.Struct(
    "<"
    "4f" # tyre wear
    "30B" # everything els
)

CAR_DAMAGE_SIZE = CAR_DAMAGE_STRUCT.size
CAR_DAMAGE_PACKET_SIZE = 1041

@dataclass(frozen=True)
class CarDamageData:
    tyres_wear: tuple[float, float, float, float]
    tyres_damage: tuple[int, int, int, int]
    brakes_damage: tuple[int, int, int, int]
    tyre_blisters: tuple[int, int, int, int]

    front_left_wing_damage: int
    front_right_wing_damage: int
    rear_wing_damage: int
    floor_damage: int
    diffuser_damage: int
    sidepod_damage: int

    drs_fault: int
    ers_fault: int

    gearbox_damage: int
    engine_damage: int

    engine_mguh_wear: int
    engine_es_wear: int
    engine_ce_wear: int
    engine_ice_wear: int
    engine_mguk_wear: int
    engine_tc_wear: int

    engine_blown: int
    engine_seized: int

    @classmethod
    def from_bytes(cls, data:bytes, offset: int) -> "CarDamageData":
        values = CAR_DAMAGE_STRUCT.unpack_from(data, offset)

        return cls(
            tyres_wear = tuple(values[0:4]),
            tyres_damage = tuple(values[4:8]),
            brakes_damage = tuple(values[8:12]),
            tyre_blisters = tuple(values[12:16]),

            front_left_wing_damage = values[16],
            front_right_wing_damage = values[17],
            rear_wing_damage = values[18],
            floor_damage = values[19],
            diffuser_damage = values[20],
            sidepod_damage = values[21],

            drs_fault = values[22],
            ers_fault = values[23],

            gearbox_damage= values[24],
            engine_damage=values[25],

            engine_mguh_wear=values[26],
            engine_es_wear=values[27],
            engine_ce_wear=values[28],
            engine_ice_wear=values[29],
            engine_mguk_wear=values[30],
            engine_tc_wear=values[31],

            engine_blown=values[32],
            engine_seized=values[33],
        )

@dataclass
class CarDamagePacket:
    header: PacketHeader
    cars: tuple[CarDamageData, ...]

    @classmethod
    def from_bytes(cls, data: bytes) -> "CarDamagePacket":
        if len(data) != CAR_DAMAGE_PACKET_SIZE:
            raise ValueError(
                f"Error: Incorrect CarDamagePacket size. Expected {CAR_DAMAGE_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        offset = HEADER_SIZE
        cars = []

        for _ in range(NUM_CARS):
            damage = CarDamageData.from_bytes(data, offset)
            cars.append(damage)
            offset += CAR_DAMAGE_SIZE

        return cls(header, cars)