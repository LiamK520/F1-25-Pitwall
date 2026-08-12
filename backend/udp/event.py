from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader

"""
//-----------------------------------------------------------------------------
// Event - 45 bytes
//-----------------------------------------------------------------------------

static const uint cs_eventStringCodeLen = 4;

// The event details packet is different for each type of event.
// Make sure only the correct type is interpreted.
union EventDataDetails
{
    struct
    {
        uint8 vehicleIdx; // Vehicle index of car achieving fastest lap
        float lapTime;    // Lap time is in seconds
    } FastestLap;

    struct
    {
        uint8 vehicleIdx; // Vehicle index of car retiring
        uint8 reason;     // Result reason - 0 = invalid, 1 = retired, 2 = finished, 3 = terminal damage, 4 = inactive, 5 = not enough laps completed, 6 = black flagged
                          // 7 = red flagged, 8 = mechanical failure, 9 = session skipped, 10 = session simulated
    } Retirement;

    struct
    {
        NEuint8 reason;     // 0 = Wet track, 1 = Safety car deployed, 2 = Red flag, 3 = Min lap not reached
    } DRSDisabled;

    struct
    {
        uint8 vehicleIdx; // Vehicle index of team mate
    } TeamMateInPits;

    struct
    {
        uint8 vehicleIdx; // Vehicle index of the race winner
    } RaceWinner;

    struct
    {
        uint8 penaltyType;        // Penalty type – see Appendices
        uint8 infringementType;   // Infringement type – see Appendices
        uint8 vehicleIdx;         // Vehicle index of the car the penalty is applied to
        uint8 otherVehicleIdx;    // Vehicle index of the other car involved
        uint8 time;               // Time gained, or time spent doing action in seconds
        uint8 lapNum;             // Lap the penalty occurred on
        uint8 placesGained;       // Number of places gained by this
    } Penalty;

    struct
    {
        uint8 vehicleIdx;                 // Vehicle index of the vehicle triggering speed trap
        float speed;                      // Top speed achieved in kilometres per hour
        uint8 isOverallFastestInSession;  // Overall fastest speed in session = 1, otherwise 0
        uint8 isDriverFastestInSession;   // Fastest speed for driver in session = 1, otherwise 0
        uint8 fastestVehicleIdxInSession; // Vehicle index of the vehicle that is the fastest in this session
        float fastestSpeedInSession;      // Speed of the vehicle that is the fastest in this session
    } SpeedTrap;

    struct
    {
        uint8 numLights;                  // Number of lights showing
    } StartLights;

    struct
    {
        uint8 vehicleIdx;                 // Vehicle index of the vehicle serving drive through
    } DriveThroughPenaltyServed;

    struct
    {
        uint8 vehicleIdx;                 // Vehicle index of the vehicle serving stop go
        float stopTime;                   // Time spent serving stop go in seconds
    } StopGoPenaltyServed;

    struct
    {
        uint32 flashbackFrameIdentifier;  // Frame identifier flashed back to
        float flashbackSessionTime;       // Session time flashed back to
    } Flashback;

    struct
    {
        uint32 buttonStatus;              // Bit flags specifying which buttons are being pressed currently - see appendices
    } Buttons;

    struct
    {
        uint8 overtakingVehicleIdx;       // Vehicle index of the vehicle overtaking
        uint8 beingOvertakenVehicleIdx;   // Vehicle index of the vehicle being overtaken
    } Overtake;

    struct
    {
        uint8 safetyCarType;              // 0 = No Safety Car, 1 = Full Safety Car, 2 = Virtual Safety Car, 3 = Formation Lap Safety Car
        uint8 eventType;                  // 0 = Deployed, 1 = Returning, 2 = Returned, 3 = Resume Race
    } SafetyCar;

    struct
    {
        uint8 vehicle1Idx;                // Vehicle index of the first vehicle involved in the collision
        uint8 vehicle2Idx;                // Vehicle index of the second vehicle involved in the collision
    } Collision;
};

struct PacketEventData
{
    // Valid event strings
    static const NEchar*    cs_sessionStartedEventCode;         // "SSTA"
    static const NEchar*    cs_sessionEndedEventCode;           // "SEND"
    static const NEchar*    cs_fastestLapEventCode;             // "FTLP"
    static const NEchar*    cs_retirementEventCode;             // "RTMT"
    static const NEchar*    cs_drsEnabledEventCode;             // "DRSE"
    static const NEchar*    cs_drsDisabledEventCode;            // "DRSD"
    static const NEchar*    cs_teamMateInPitsEventCode;         // "TMPT"
    static const NEchar*    cs_chequeredFlagEventCode;          // "CHQF"
    static const NEchar*    cs_raceWinnerEventCode;             // "RCWN"
    static const NEchar*    cs_penaltyEventCode;                // "PENA"
    static const NEchar*    cs_speedTrapEventCode;              // "SPTP"
    static const NEchar*    cs_startLightsEventCode;            // "STLG"
    static const NEchar*    cs_lightsOutEventCode;              // "LGOT"
    static const NEchar*    cs_driveThroughServedEventCode;     // "DTSV"
    static const NEchar*    cs_stopGoServedEventCode;           // "SGSV"
    static const NEchar*    cs_flashbackEventCode;              // "FLBK"
    static const NEchar*    cs_buttonStatusEventCode;           // "BUTN"
    static const NEchar*    cs_redFlagEventCode;                // "RDFL"
    static const NEchar*    cs_overtakeEventCode;               // "OVTK"
    static const NEchar*    cs_safetyCarEventCode;              // "SCAR"
    static const NEchar*    cs_collisionEventCode;              // "COLL"

    PacketHeader        m_header;               // Header

    // Packet specific data
    uint8               m_eventStringCode[cs_eventStringCodeLen];       // Event string code
    EventDataDetails    m_eventDetails;                                 // Event details - should be interpreted differently for each type
};"""

EVENT_PACKET_SIZE = 45
EVENT_CODE_SIZE = 4
EVENT_DETAILS_SIZE = 12

# all event types

# declaring these struct headers here instead of just using the raw string later in case they need updated in future
# to support new udp versions
# probably could use raw strings due to short length but still

FASTEST_LAP_STRUCT = struct.Struct("<Bf")

@dataclass(frozen=True)
class FastestLapEvent:
    vehicle_idx: int
    lap_time: float


RETIREMENT_STRUCT = struct.Struct("<BB")
@dataclass(frozen=True)
class RetirementEvent:
    vehicle_idx: int
    reason: int


DRS_DISABLED_STRUCT = struct.Struct("<B")
@dataclass(frozen=True)
class DRSDisabledEvent:
    reason: int


TEAMMATE_IN_PITS_STRUCT = struct.Struct("<B")
@dataclass(frozen=True)
class TeamMateInPitsEvent:
    vehicle_idx: int


RACE_WINNER_STRUCT = struct.Struct("<B")
@dataclass(frozen=True)
class RaceWinnerEvent:
    vehicle_idx: int


PENALTY_STRUCT = struct.Struct("<7B")
@dataclass(frozen=True)
class PenaltyEvent:
    penalty_type: int
    infringement_type: int
    vehicle_idx: int
    other_vehicle_idx: int
    time: int
    lap_num: int
    places_gained: int


SPEED_TRAP_STRUCT = struct.Struct("<BfBBBf")
@dataclass(frozen=True)
class SpeedTrapEvent:
    vehicle_idx: int
    speed: float
    is_overall_fastest_in_session: int
    is_driver_fastest_in_session: int
    fastest_vehicle_idx_in_session: int
    fastest_speed_in_session: float


START_LIGHTS_STRUCT = struct.Struct("<B")
@dataclass(frozen=True)
class StartLightsEvent:
    num_lights: int


DRIVE_THROUGH_SERVED_STRUCT = struct.Struct("<B")
@dataclass(frozen=True)
class DriveThroughServedEvent:
    vehicle_idx: int


STOP_GO_SERVED_STRUCT = struct.Struct("<Bf")
@dataclass(frozen=True)
class StopGoServedEvent:
    vehicle_idx: int
    stop_time: float


FLASHBACK_STRUCT = struct.Struct("<If")
@dataclass(frozen=True)
class FlashbackEvent:
    flashback_frame_identifier: int
    flashback_session_time: float



BUTTON_STRUCT = struct.Struct("<I")
@dataclass(frozen=True)
class ButtonsEvent:
    button_status: int


OVERTAKE_STRUCT = struct.Struct("<BB")
@dataclass(frozen=True)
class OvertakeEvent:
    overtaking_vehicle_idx: int
    being_overtaken_vehicle_idx: int


SAFETY_CAR_STRUCT = struct.Struct("<BB")
@dataclass(frozen=True)
class SafetyCarEvent:
    safety_car_type: int
    event_type: int


COLLISION_STRUCT = struct.Struct("<BB")
@dataclass(frozen=True)
class CollisionEvent:
    vehicle1_idx: int
    vehicle2_idx: int


# union type fo all event
EventDetails = (
    FastestLapEvent
    | RetirementEvent
    | DRSDisabledEvent
    | TeamMateInPitsEvent
    | RaceWinnerEvent
    | PenaltyEvent
    | SpeedTrapEvent
    | StartLightsEvent
    | DriveThroughServedEvent
    | StopGoServedEvent
    | FlashbackEvent
    | ButtonsEvent
    | OvertakeEvent
    | SafetyCarEvent
    | CollisionEvent
    | None
)


# event packet#

def parse_event_details(event_code: str, data: bytes, offset: int):
    if event_code == "FTLP":
        vehicle_idx, lap_time = FASTEST_LAP_STRUCT.unpack_from(data, offset)
        return FastestLapEvent(
            vehicle_idx=vehicle_idx,
            lap_time=lap_time,
        )

    if event_code == "RTMT":
        vehicle_idx, reason = RETIREMENT_STRUCT.unpack_from(data, offset)
        return RetirementEvent(
            vehicle_idx=vehicle_idx,
            reason=reason,
        )

    if event_code == "DRSD":
        reason = DRS_DISABLED_STRUCT.unpack_from(data, offset)

        return DRSDisabledEvent(reason=reason)

    if event_code == "TMPT":
        vehicle_idx = TEAMMATE_IN_PITS_STRUCT.unpack_from(data, offset)

        return TeamMateInPitsEvent(
            vehicle_idx=vehicle_idx,
        )

    if event_code == "RCWN":
        vehicle_idx = RACE_WINNER_STRUCT.unpack_from(data, offset)

        return RaceWinnerEvent(
            vehicle_idx=vehicle_idx,
        )

    if event_code == "PENA":
        values = PENALTY_STRUCT.unpack_from(data, offset)
        return PenaltyEvent(*values)

    if event_code == "SPTP":
        values = SPEED_TRAP_STRUCT.unpack_from(data,offset)

        return SpeedTrapEvent(*values)

    if event_code == "STLG":
        (num_lights,) = START_LIGHTS_STRUCT.unpack_from(data, offset)
        return StartLightsEvent(
            num_lights=num_lights,
        )

    if event_code == "DTSV":
        (vehicle_idx,) =DRIVE_THROUGH_SERVED_STRUCT.unpack_from(data, offset)
        return DriveThroughServedEvent(
            vehicle_idx=vehicle_idx,
        )

    if event_code == "SGSV":
        vehicle_idx, stop_time = STOP_GO_SERVED_STRUCT.unpack_from(data, offset)
        return StopGoServedEvent(
            vehicle_idx=vehicle_idx,
            stop_time=stop_time,
        )

    if event_code == "FLBK":
        frame_identifier, session_time = FLASHBACK_STRUCT.unpack_from(data, offset)
        return FlashbackEvent(
            flashback_frame_identifier=frame_identifier,
            flashback_session_time=session_time,
        )

    if event_code == "BUTN":
        (button_status,) = BUTTON_STRUCT.unpack_from(data, offset)
        return ButtonsEvent(
            button_status=button_status,
        )

    if event_code == "OVTK":
        overtaking, overtaken = OVERTAKE_STRUCT.unpack_from(data, offset)
        return OvertakeEvent(
            overtaking_vehicle_idx=overtaking,
            being_overtaken_vehicle_idx=overtaken,
        )

    if event_code == "SCAR":
        safety_car_type, event_type = SAFETY_CAR_STRUCT.unpack_from(data, offset)
        return SafetyCarEvent(
            safety_car_type=safety_car_type,
            event_type=event_type,
        )

    if event_code == "COLL":
        vehicle1, vehicle2 = COLLISION_STRUCT.unpack_from(data, offset)

        return CollisionEvent(
            vehicle1_idx=vehicle1,
            vehicle2_idx=vehicle2,
        )

    # these all have no extra data

    if event_code in {
        "SSTA",     # session started
        "SEND",     # session ended
        "DRSE",     # DRS enabled
        "CHQF",     # chequered flag
        "LGOT",     # lights out
        "RDFL",     # red flag
    }:
        return None

    raise ValueError(f"Unknown event code: {event_code}")

@dataclass(frozen=True)
class EventPacket:
    header: PacketHeader
    event_code: str
    details: EventDetails

    @classmethod
    def from_bytes(cls, data: bytes) -> "EventPacket":
        if len(data) != EVENT_PACKET_SIZE:
            raise ValueError(
                f"Error: Incorrect EventPacket size. "
                f"Expected {EVENT_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        code_offset = HEADER_SIZE
        details_offset = code_offset + EVENT_CODE_SIZE

        event_code = data[code_offset:details_offset].decode("ascii")

        details = parse_event_details(event_code, data, details_offset)

        return cls(header, event_code, details)


