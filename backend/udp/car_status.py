from dataclasses import dataclass
import struct

from udp.constants import NUM_CARS
from udp.header import HEADER_SIZE, PacketHeader

"""
//-----------------------------------------------------------------------------
// Car Status - 1239 bytes
//-----------------------------------------------------------------------------

//-----------------------------------------------------------------------------
// Car status data for one car
//-----------------------------------------------------------------------------
struct CarStatusData
{
    uint8       m_tractionControl;                  // Traction control - 0 = off, 1 = medium, 2 = full
    uint8       m_antiLockBrakes;                   // 0 (off) - 1 (on)
    uint8       m_fuelMix;                          // Fuel mix - 0 = lean, 1 = standard, 2 = rich, 3 = max
    uint8       m_frontBrakeBias;                   // Front brake bias (percentage)
    uint8       m_pitLimiterStatus;                 // Pit limiter status - 0 = off, 1 = on
    float       m_fuelInTank;                       // Current fuel mass
    float       m_fuelCapacity;                     // Fuel capacity
    float       m_fuelRemainingLaps;                // Fuel remaining in terms of laps (value on MFD)
    uint16      m_maxRPM;                           // Cars max RPM, point of rev limiter
    uint16      m_idleRPM;                          // Cars idle RPM
    uint8       m_maxGears;                         // Maximum number of gears
    uint8       m_drsAllowed;                       // 0 = not allowed, 1 = allowed
    uint16      m_drsActivationDistance;            // 0 = DRS not available, non-zero - DRS will be available in [X] metres
    uint8       m_actualTyreCompound;               // F1 Modern - 16 = C5, 17 = C4, 18 = C3, 19 = C2, 20 = C1, 21 = C0, 22 = C6, 7 = inter, 8 = wet
                                                    // F1 Classic - 9 = dry, 10 = wet
                                                    // F2 – 11 = super soft, 12 = soft, 13 = medium, 14 = hard, 15 = wet
    uint8       m_visualTyreCompound;               // F1 visual (can be different from actual compound)
                                                    // 16 = soft, 17 = medium, 18 = hard, 7 = inter, 8 = wet
                                                    // F1 Classic – same as above
                                                    // F2 ‘20, 15 = wet, 19 – super soft, 20 = soft, 21 = medium, 22 = hard
    uint8       m_tyresAgeLaps;                     // Age in laps of the current set of tyres
    int8        m_vehicleFIAFlags;                  // -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
    float       m_enginePowerICE;                   // Engine power output of ICE (W)
    float       m_enginePowerMGUK;                  // Engine power output of MGU-K (W)
    float       m_ersStoreEnergy;                   // ERS energy store in Joules
    uint8       m_ersDeployMode;                    // ERS deployment mode, 0 = none, 1 = medium, 2 = hotlap, 3 = overtake
    float       m_ersHarvestedThisLapMGUK;          // ERS energy harvested this lap by MGU-K
    float       m_ersHarvestedThisLapMGUH;          // ERS energy harvested this lap by MGU-H
    float       m_ersDeployedThisLap;               // ERS energy deployed this lap
    uint8       m_networkPaused;                    // Whether the car is paused in a network game
};

struct PacketCarStatusData
{
    PacketHeader    m_header;               // Header

    // Packet specific data
    CarStatusData       m_carStatusData[cs_maxNumCarsInUDPData];      // data for all cars on track
};
"""

CAR_STATUS_STRUCT = struct.Struct(
    "<"
    "5B"      # tc to pit limiter
    "3f"      # fuel, capacity and remaining laps
    "2H"      # max RPM, idle RPM
    "2B"      # max gears, DRS allowed
    "H"       # DRS activation distance
    "3B"      # actual compound, visual compound and tyre age
    "b"       # FIA flag
    "3f"      # ICE power, MGU-K power, ERS store
    "B"       # ERS deploy mode
    "3f"      # ERS harvested MGU-K, MGU-H, deployed
    "B"       # network paused
)

CAR_STATUS_SIZE = CAR_STATUS_STRUCT.size

CAR_STATUS_PACKET_SIZE = 1239

@dataclass(frozen=True)
class CarStatusData:
    traction_control: int
    anti_lock_brakes: int
    fuel_mix: int
    front_brake_bias: int
    pit_limiter_status: int

    fuel_in_tank: float
    fuel_capacity: float
    fuel_remaining_laps: float

    max_rpm: int
    idle_rpm: int
    max_gears: int

    drs_allowed: int
    drs_activation_distance: int

    actual_tyre_compound: int
    visual_tyre_compound: int
    tyres_age_laps: int

    vehicle_fia_flags: int

    engine_power_ice: float
    engine_power_mguk: float

    ers_store_energy: float
    ers_deploy_mode: int

    ers_harvested_this_lap_mguk: float
    ers_harvested_this_lap_mguh: float
    ers_deployed_this_lap: float

    network_paused: int

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "CarStatusData":
        values = CAR_STATUS_STRUCT.unpack_from(data, offset)
        return cls(*values)


@dataclass(frozen=True)
class CarStatusPacket:
    header: PacketHeader
    cars: tuple[CarStatusData, ...]

    @classmethod
    def from_bytes(cls, data: bytes) -> "CarStatusPacket":
        if len(data) != CAR_STATUS_PACKET_SIZE:
            raise ValueError(
                f"Error: Incorrect CarStatusPacket size. Expected {CAR_STATUS_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        offset = HEADER_SIZE
        cars = []

        for _ in range(NUM_CARS):
            status = CarStatusData.from_bytes(data, offset)
            cars.append(status)
            offset += CAR_STATUS_SIZE

        return cls(header, tuple(cars))        