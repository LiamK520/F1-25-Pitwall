from dataclasses import dataclass
import struct

from udp.header import HEADER_SIZE, PacketHeader

"""
//-----------------------------------------------------------------------------
// Session - 753 bytes
//-----------------------------------------------------------------------------
static const uint32     cs_maxMarshalsZonePerLap = 21;
static const uint32     cs_maxWeatherForecastSamples = 64;
static const uint32     cs_maxSessionsInWeekend = 12;

struct MarshalZone
{
    float       m_zoneStart;       // Fraction (0..1) of way through the lap the marshal zone starts
    int8        m_zoneFlag;        // -1 = invalid/unknown, 0 = none, 1 = green, 2 = blue, 3 = yellow
};

struct WeatherForecastSample
{
    uint8       m_sessionType;              // 0 = unknown, see appendix
    uint8       m_timeOffset;               // Time in minutes the forecast is for
    uint8       m_weather;                  // Weather - 0 = clear, 1 = light cloud, 2 = overcast, 3 = light rain, 4 = heavy rain, 5 = storm
    int8        m_trackTemperature;         // Track temp. in degrees celsius
    int8        m_trackTemperatureChange;   // Track temp. change - 0 = up, 1 = down, 2 = no change
    int8        m_airTemperature;           // Air temp. in degrees celsius
    int8        m_airTemperatureChange;     // Air temp. change - 0 = up, 1 = down, 2 = no change
    uint8       m_rainPercentage;           // Rain percentage (0-100)
};

struct PacketSessionData
{
    PacketHeader    m_header;               // Header

    // Packet specific data
    uint8       m_weather;                          // Weather - 0 = clear, 1 = light cloud, 2 = overcast, 3 = light rain, 4 = heavy rain, 5 = storm
    int8        m_trackTemperature;                 // Track temp. in degrees celsius
    int8        m_airTemperature;                   // Air temp. in degrees celsius
    uint8       m_totalLaps;                        // Total number of laps in this race
    uint16      m_trackLength;                      // Track length in metres
    uint8       m_sessionType;                      // 0 = unknown, see appendix
    int8        m_trackId;                          // -1 for unknown, see appendix
    uint8       m_formula;                          // Formula, 0 = F1 Modern, 1 = F1 Classic, 2 = F2, 3 = F1 Generic, 4 = Beta, 6 = Esports, 8 = F1 World, 9 = F1 Elimination
    uint16      m_sessionTimeLeft;		            // Time left in session in seconds
    uint16      m_sessionDuration;		            // Session duration in seconds
    uint8       m_pitSpeedLimit;                    // Pit speed limit in kilometres per hour
    uint8       m_gamePaused;                       // Whether the game is paused - network game only
    uint8       m_isSpectating;                     // Whether the player is spectating
    uint8       m_spectatorCarIndex;                // Index of the car being spectated
    uint8       m_sliProNativeSupport;              // SLI Pro support, 0 = inactive, 1 = active
    uint8       m_numMarshalZones;                  // Number of marshal zones to follow
    MarshalZone m_marshalZones[cs_maxMarshalsZonePerLap];  // List of marshal zones - max 21
    uint8       m_safetyCarStatus;                  // 0 = no safety car, 1 = full, 2 = virtual, 3 = formation lap
    uint8       m_networkGame;                      // 0 = offline, 1 = online
    uint8       m_numWeatherForecastSamples;        // Number of weather samples to follow
    WeatherForecastSample m_weatherForecastSamples[cs_maxWeatherForecastSamples];   // Array of weather forecast samples
    uint8       m_forecastAccuracy;                 // 0 = Perfect, 1 = Approximate
    uint8       m_aiDifficulty;                     // AI difficulty - 0-110
    uint32      m_seasonLinkIdentifier;             // Identifier for season - persists across saves
    uint32      m_weekendLinkIdentifier;            // Identifier for weekend - persists across saves
    uint32      m_sessionLinkIdentifier;            // Identifier for session - persists across saves
    uint8       m_pitStopWindowIdealLap;            // Ideal lap to pit on for current strategy (player)
    uint8       m_pitStopWindowLatestLap;           // Latest lap to pit on for current strategy (player)
    uint8       m_pitStopRejoinPosition;            // Predicted position to rejoin at (player)
    uint8       m_steeringAssist;                   // 0 = off, 1 = on
    uint8       m_brakingAssist;                    // 0 = off, 1 = low, 2 = medium, 3 = high
    uint8       m_gearboxAssist;                    // 1 = manual, 2 = manual & suggested gear, 3 = auto
    uint8       m_pitAssist;                        // 0 = off, 1 = on
    uint8       m_pitReleaseAssist;                 // 0 = off, 1 = on
    uint8       m_ERSAssist;                        // 0 = off, 1 = on
    uint8       m_DRSAssist;                        // 0 = off, 1 = on
    uint8       m_dynamicRacingLine;                // 0 = off, 1 = corners only, 2 = full
    uint8       m_dynamicRacingLineType;            // 0 = 2D, 1 = 3D
    uint8       m_gameMode;                         // Game mode id - see appendix
    uint8       m_ruleSet;                          // Ruleset - see appendix
    uint32      m_timeOfDay;                        // Local time of day - minutes since midnight
    uint8       m_sessionLength;                    // 0 = None, 2 = Very Short, 3 = Short, 4 = Medium, 5 = Medium Long, 6 = Long, 7 = Full
    uint8       m_speedUnitsLeadPlayer;             // 0 = MPH, 1 = KPH
    uint8       m_temperatureUnitsLeadPlayer;       // 0 = Celsius, 1 = Fahrenheit
    uint8       m_speedUnitsSecondaryPlayer;        // 0 = MPH, 1 = KPH
    uint8       m_temperatureUnitsSecondaryPlayer;  // 0 = Celsius, 1 = Fahrenheit
    uint8       m_numSafetyCarPeriods;              // Number of safety cars called during session
    uint8       m_numVirtualSafetyCarPeriods;       // Number of virtual safety cars called during session
    uint8       m_numRedFlagPeriods;                // Number of red flags called during session
    uint8       m_equalCarPerformance;              // 0 = Off, 1 = On
    uint8       m_recoveryMode;                     // 0 = None, 1 = Flashbacks, 2 = Auto-recovery
    uint8       m_flashbackLimit;                   // 0 = Low, 1 = Medium, 2 = High, 3 = Unlimited
    uint8       m_surfaceType;                      // 0 = Simplified, 1 = Realistic
    uint8       m_lowFuelMode;                      // 0 = Easy, 1 = Hard
    uint8       m_raceStarts;                       // 0 = Manual, 1 = Assisted
    uint8       m_tyreTemperature;                  // 0 = Surface only, 1 = Surface & Carcass
    uint8       m_pitLaneTyreSim;                   // 0 = On, 1 = Off
    uint8       m_carDamage;                        // 0 = Off, 1 = Reduced, 2 = Standard, 3 = Simulation
    uint8       m_carDamageRate;                    // 0 = Reduced, 1 = Standard, 2 = Simulation
    uint8       m_collisions;                       // 0 = Off, 1 = Player-to-Player Off, 2 = On
    uint8       m_collisionsOffForFirstLapOnly;     // 0 = Disabled, 1 = Enabled
    uint8       m_mpUnsafePitRelease;               // 0 = On, 1 = Off (Multiplayer)
    uint8       m_mpOffForGriefing;                 // 0 = Disabled, 1 = Enabled (Multiplayer)
    uint8       m_cornerCuttingStringency;          // 0 = Regular, 1 = Strict
    uint8       m_parcFermeRules;                   // 0 = Off, 1 = On
    uint8       m_pitStopExperience;                // 0 = Automatic, 1 = Broadcast, 2 = Immersive
    uint8       m_safetyCar;                        // 0 = Off, 1 = Reduced, 2 = Standard, 3 = Increased
    uint8       m_safetyCarExperience;              // 0 = Broadcast, 1 = Immersive
    uint8       m_formationLap;                     // 0 = Off, 1 = On
    uint8       m_formationLapExperience;           // 0 = Broadcast, 1 = Immersive
    uint8       m_redFlags;                         // 0 = Off, 1 = Reduced, 2 = Standard, 3 = Increased
    uint8       m_affectsLicenceLevelSolo;          // 0 = Off, 1 = On
    uint8       m_affectsLicenceLevelMP;            // 0 = Off, 1 = On
    uint8       m_numSessionsInWeekend;             // Number of session in following array
    uint8       m_weekendStructure[cs_maxSessionsInWeekend];    // List of session types to show weekend structure - see appendix for types
    float       m_sector2LapDistanceStart;          // Distance in m around track where sector 2 starts
    float       m_sector3LapDistanceStart;          // Distance in m around track where sector 3 starts
};
"""

MAX_MARSHAL_ZONES = 21
MAX_WEATHER_FORECAST_SAMPLES = 64
MAX_SESSIONS_IN_WEEKEND = 12

SESSION_PACKET_SIZE = 753

# marshal

MARSHAL_ZONE_STRUCT = struct.Struct("<fb")
MARSHAL_ZONE_SIZE = MARSHAL_ZONE_STRUCT.size


@dataclass(frozen=True)
class MarshalZone:
    zone_start: float
    zone_flag: int

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "MarshalZone":
        values = MARSHAL_ZONE_STRUCT.unpack_from(data, offset)
        return cls(*values)


# weather

WEATHER_FORECAST_STRUCT = struct.Struct("<3B4bB")
WEATHER_FORECAST_SIZE = WEATHER_FORECAST_STRUCT.size

@dataclass(frozen=True)
class WeatherForecastSample:
    session_type: int
    time_offset: int
    weather: int

    track_temperature: int
    track_temperature_change: int

    air_temperature: int
    air_temperature_change: int

    rain_percentage: int

    @classmethod
    def from_bytes(cls, data: bytes, offset: int) -> "WeatherForecastSample":
        values = WEATHER_FORECAST_STRUCT.unpack_from(data, offset)
        return cls(*values)


# session

SESSION_STRUCT = struct.Struct(
     "<"
    "B"       # weather
    "b"       # track temp
    "b"       # air temp
    "B"       # total laps
    "H"       # track length
    "B"       # session type
    "b"       # track ID
    "B"       # formula
    "H"       # session time left
    "H"       # session duration
    "B"       # pit speed limit
    "B"       # game paused
    "B"       # is spectating
    "B"       # spectator car index
    "B"       # sli pro native
    "B"       # number of marshal zones

    # using padding bytes here to account for marshal zones, we will manually fill this later
    # fixed amount of space but we may not use all of it 

    f"{MAX_MARSHAL_ZONES * MARSHAL_ZONE_SIZE}x"

    "B"       # safety car status
    "B"       # network game
    "B"       # no. weather forecast samples

    # same here

    f"{MAX_WEATHER_FORECAST_SAMPLES * WEATHER_FORECAST_SIZE}x"

    "B"       # forecast accuracy
    "B"       # ai dificulty

    "3I"     # season, weekend, session link identifiers

    "3B"      # ideal pit lap, latest pit lap, rejoin position

    "9B"      # assist setings

    "B"       # game mode
    "B"       # rule set
    "I"       # time of day
    "B"       # session length

    "4B"      # player unit settings

    "3B"      # SC, VSC and red flag period counts

    "24B"     # simulation and rules settings

    "B"       # number of sessions in weekend
    "12B"     # weekend structure

    "ff"      # sector 2 and sector 3 start distances
)

SESSION_SIZE = SESSION_STRUCT.size

@dataclass(frozen=True)
class SessionPacket:
    header: PacketHeader

    weather: int
    track_temperature: int
    air_temperature: int

    total_laps: int
    track_length: int

    session_type: int
    track_id: int
    formula: int

    session_time_left: int
    session_duration: int

    pit_speed_limit: int

    game_paused: int
    is_spectating: int
    spectator_car_index: int
    sli_pro_native_support: int

    # probably redundant to store this but it doesnt hurt
    num_marshal_zones: int
    marshal_zones: tuple[MarshalZone, ...]

    safety_car_status: int
    network_game: int

    #same
    num_weather_forecast_samples: int
    weather_forecast_samples: tuple[WeatherForecastSample, ...]

    forecast_accuracy: int
    ai_difficulty: int

    season_link_identifier: int
    weekend_link_identifier: int
    session_link_identifier: int

    pit_stop_window_ideal_lap: int
    pit_stop_window_latest_lap: int
    pit_stop_rejoin_position: int

    steering_assist: int
    braking_assist: int
    gearbox_assist: int
    pit_assist: int
    pit_release_assist: int
    ers_assist: int
    drs_assist: int
    dynamic_racing_line: int
    dynamic_racing_line_type: int

    game_mode: int
    rule_set: int

    time_of_day: int
    session_length: int

    speed_units_lead_player: int
    temperature_units_lead_player: int
    speed_units_secondary_player: int
    temperature_units_secondary_player: int

    num_safety_car_periods: int
    num_virtual_safety_car_periods: int
    num_red_flag_periods: int

    equal_car_performance: int
    recovery_mode: int
    flashback_limit: int
    surface_type: int
    low_fuel_mode: int
    race_starts: int
    tyre_temperature: int
    pit_lane_tyre_sim: int
    car_damage: int
    car_damage_rate: int
    collisions: int
    collisions_off_for_first_lap_only: int
    mp_unsafe_pit_release: int
    mp_off_for_griefing: int
    corner_cutting_stringency: int
    parc_ferme_rules: int
    pit_stop_experience: int
    safety_car: int
    safety_car_experience: int
    formation_lap: int
    formation_lap_experience: int
    red_flags: int
    affects_licence_level_solo: int
    affects_licence_level_mp: int

    # may also be redundant but keep for now
    num_sessions_in_weekend: int
    weekend_structure: tuple[int, ...]

    sector2_lap_distance_start: float
    sector3_lap_distance_start: float

    @classmethod
    def from_bytes(cls, data: bytes) -> "SessionPacket":
        if len(data) != SESSION_PACKET_SIZE:
            raise ValueError(
                f"Error: Invalid Session packet size. Expected {SESSION_PACKET_SIZE} but got {len(data)}"
            )

        header = PacketHeader.from_bytes(data)

        values = SESSION_STRUCT.unpack_from(data, HEADER_SIZE)

        num_marshal_zones = values[15]
        num_weather_forecast_samples = values[18]
        num_sessions_in_weekend = values[71]

        if num_marshal_zones > MAX_MARSHAL_ZONES:
            raise ValueError(
                f"Invalid number of marshal zones: {num_marshal_zones}"
            )

        if num_weather_forecast_samples > MAX_WEATHER_FORECAST_SAMPLES:
            raise ValueError(
                f"Invalid number of weather forecast samples: {num_weather_forecast_samples}"
            )

        if num_sessions_in_weekend > MAX_SESSIONS_IN_WEEKEND:
            raise ValueError(
                f"Invalid number of sessions in weekend: {num_sessions_in_weekend}"
            )

        # marshal starts after max attr
        marshal_offset = HEADER_SIZE + 19
        marshal_zones = []

        # after marshal zones there is sc status, network game and count then samples
        weather_offset = marshal_offset + MAX_MARSHAL_ZONES * MARSHAL_ZONE_SIZE + 3
        weather_forecast_samples = []

        for i in range(num_marshal_zones):
            offset = marshal_offset + i * MARSHAL_ZONE_SIZE
            marshal_zones.append(MarshalZone.from_bytes(data, offset))

        for i in range(num_weather_forecast_samples):
            offset = weather_offset + i * WEATHER_FORECAST_SIZE
            weather_forecast_samples.append(WeatherForecastSample.from_bytes(data, offset))

        weekend_structure = tuple(values[72:72 + num_sessions_in_weekend])

        # very long return. maybe see if there is a better way to do this i doubt it though
        return cls(
            header=header,

            weather=values[0],
            track_temperature=values[1],
            air_temperature=values[2],

            total_laps=values[3],
            track_length=values[4],

            session_type=values[5],
            track_id=values[6],
            formula=values[7],

            session_time_left=values[8],
            session_duration=values[9],

            pit_speed_limit=values[10],

            game_paused=values[11],
            is_spectating=values[12],
            spectator_car_index=values[13],
            sli_pro_native_support=values[14],

            num_marshal_zones = num_marshal_zones,
            marshal_zones=tuple(marshal_zones),

            safety_car_status=values[16],
            network_game=values[17],

            num_weather_forecast_samples = num_weather_forecast_samples,
            weather_forecast_samples=tuple(
                weather_forecast_samples
            ),

            forecast_accuracy=values[19],
            ai_difficulty=values[20],

            season_link_identifier=values[21],
            weekend_link_identifier=values[22],
            session_link_identifier=values[23],

            pit_stop_window_ideal_lap=values[24],
            pit_stop_window_latest_lap=values[25],
            pit_stop_rejoin_position=values[26],

            steering_assist=values[27],
            braking_assist=values[28],
            gearbox_assist=values[29],
            pit_assist=values[30],
            pit_release_assist=values[31],
            ers_assist=values[32],
            drs_assist=values[33],
            dynamic_racing_line=values[34],
            dynamic_racing_line_type=values[35],

            game_mode=values[36],
            rule_set=values[37],

            time_of_day=values[38],
            session_length=values[39],

            speed_units_lead_player=values[40],
            temperature_units_lead_player=values[41],
            speed_units_secondary_player=values[42],
            temperature_units_secondary_player=values[43],

            num_safety_car_periods=values[44],
            num_virtual_safety_car_periods=values[45],
            num_red_flag_periods=values[46],

            equal_car_performance=values[47],
            recovery_mode=values[48],
            flashback_limit=values[49],
            surface_type=values[50],
            low_fuel_mode=values[51],
            race_starts=values[52],
            tyre_temperature=values[53],
            pit_lane_tyre_sim=values[54],
            car_damage=values[55],
            car_damage_rate=values[56],
            collisions=values[57],
            collisions_off_for_first_lap_only=values[58],
            mp_unsafe_pit_release=values[59],
            mp_off_for_griefing=values[60],
            corner_cutting_stringency=values[61],
            parc_ferme_rules=values[62],
            pit_stop_experience=values[63],
            safety_car=values[64],
            safety_car_experience=values[65],
            formation_lap=values[66],
            formation_lap_experience=values[67],
            red_flags=values[68],
            affects_licence_level_solo=values[69],
            affects_licence_level_mp=values[70],

            num_sessions_in_weekend = num_sessions_in_weekend,
            weekend_structure=weekend_structure,

            sector2_lap_distance_start=values[84],
            sector3_lap_distance_start=values[85],
        )