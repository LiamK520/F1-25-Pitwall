from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader
from udp.constants import NUM_CARS

"""
//-----------------------------------------------------------------------------
// Participants - 1284 bytes
//-----------------------------------------------------------------------------

// RGB value of a colour
struct LiveryColour
{
    uint8       red;
    uint8       green;
    uint8       blue;
};

//-----------------------------------------------------------------------------
// Data about one participant
//-----------------------------------------------------------------------------
struct ParticipantData
{
    uint8           m_aiControlled;                     // Whether the vehicle is AI (1) or Human (0) controlled
    uint8           m_driverId;                         // Driver id - see appendix, 255 if network human
    uint8           m_networkId;                        // Network id - unique identifier for network players
    uint8           m_teamId;                           // Team id - see appendix
    uint8           m_myTeam;                           // My team flag - 1 = My Team, 0 = otherwise
    uint8           m_raceNumber;                       // Race number of the car
    uint8           m_nationality;                      // Nationality of the driver
    char            m_name[cs_maxParticipantNameLen];   // Name of participant in UTF-8 format – null terminated
                                                        // Will be truncated with ... (U+2026) if too long
    uint8           m_yourTelemetry;                    // The player's UDP setting, 0 = restricted, 1 = public
    uint8           m_showOnlineNames;                  // The player's show online names setting, 0 = off, 1 = on
    uint16          m_techLevel;                        // F1 World tech level
    uint8           m_platform;                         // 1 = Steam, 3 = PlayStation, 4 = Xbox, 6 = Origin, 255 = unknown
    uint8           m_numColours;                       // Number of colours valid for this car
    LiveryColour    m_liveryColours[4];                 // Colours for the car
};

struct PacketParticipantsData
{
    PacketHeader    m_header;                       // Header

    // Packet specific data
    uint8               m_numActiveCars;            // Number of active cars in the data - should match number of cars on HUD
    ParticipantData     m_participants[cs_maxNumCarsInUDPData];
};
"""

PARTICIPANT_NAME_LENGTH = 32

PARTICIPANT_STRUCT = struct.Struct(
    "<"
    "BBBBBBB" # AI to nationality
    "32s" # names
    "BBHBB" # telem to num colours
    "12B" # livery colours
)

PARTICIPANT_SIZE = PARTICIPANT_STRUCT.size

PARTICIPANTS_PACKET_SIZE = 1284

@dataclass(frozen=True)
class LiveryColour:
    red: int
    green: int
    blue: int


@dataclass(frozen=True)
class ParticipantData:
    ai_controlled: int
    driver_id: int
    network_id: int
    team_id: int
    my_team: int
    race_number: int
    nationality: int

    name: str

    your_telemetry: int
    show_online_names: int
    tech_level: int
    platform: int

    livery_colours: tuple[LiveryColour, ...]

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "ParticipantData":
        values = PARTICIPANT_STRUCT.unpack_from(data, offset)

        name_bytes = values[7]

        # decode name from null terminated utf8 format
        name = name_bytes.split(b"\x00", 1)[0].decode("utf-8", errors="replace")

        num_colours = values[12]
        colour_values = values[13:]

        colours = []

        # log all colours regardless of num colours for now. can filter out somewhere later
        for i in range(4):
            base = i * 3

            colours.append(
                LiveryColour(
                    red=colour_values[base],
                    green=colour_values[base + 1],
                    blue=colour_values[base + 2],
                )
            )

        # messy but necessary
        return cls(
            ai_controlled=values[0],
            driver_id=values[1],
            network_id=values[2],
            team_id=values[3],
            my_team=values[4],
            race_number=values[5],
            nationality=values[6],
            name=name,
            your_telemetry=values[8],
            show_online_names=values[9],
            tech_level=values[10],
            platform=values[11],
            livery_colours=tuple(colours[:num_colours]),
        )


@dataclass(frozen=True)
class ParticipantsPacket:
    header: PacketHeader
    num_active_cars: int
    participants: tuple[ParticipantData, ...]

    @classmethod
    def from_bytes(cls, data: bytes) ->  "ParticipantsPacket":
        if len(data) != PARTICIPANTS_PACKET_SIZE:
            raise ValueError(
                f"Error: Invalid Participants packet size. Expected {PARTICIPANTS_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        num_active_cars = data[HEADER_SIZE]

        participants = []
        offset = HEADER_SIZE + 1

        for _ in range(NUM_CARS):
            participant = ParticipantData.from_bytes(data, offset)
            participants.append(participant)
            offset += PARTICIPANT_SIZE

        return cls(
            header=header,
            num_active_cars=num_active_cars,
            participants=tuple(participants)
        )