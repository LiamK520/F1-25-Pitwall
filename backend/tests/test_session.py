import struct

import pytest

from tests.helpers import make_header
from udp.packet_id import PacketId
from udp.session import MARSHAL_ZONE_SIZE, MAX_MARSHAL_ZONES, MAX_SESSIONS_IN_WEEKEND,  \
    MAX_WEATHER_FORECAST_SAMPLES, SESSION_PACKET_SIZE, SESSION_SIZE, WEATHER_FORECAST_SIZE, \
        MarshalZone, SessionPacket, WeatherForecastSample

# creation funcs

def make_marshal_zone(
    zone_start: float = 0.25,
    zone_flag: int = 3,
) -> bytes:
    return struct.pack(
        "<fb",
        zone_start,
        zone_flag,
    )

def make_weather_sample(
    session_type: int = 15,
    time_offset: int = 5,
    weather: int = 0,
) -> bytes:
    return struct.pack(
        "<BBBbbbbB",
        session_type,
        time_offset,
        weather,
        25,     # track temperature
        2,      # track temperature change - no change
        18,     # air temperature
        2,      # air temperature change - no change
        10,     # rain percentage
    )


def make_session_packet() -> bytes:
    data = make_header(PacketId.SESSION)

    # session fields before marshal zones
    data += struct.pack(
        "<BbbBHBbBHHBBBBBB",
        0,      # weather - clear
        25,     # track temperature
        18,     # air temperature
        5,      # total laps
        5891,   # track length
        15,     # session type - race
        7,      # track ID - Silverstone
        0,      # formula - F1 modern
        900,    # session time left
        1200,   # session duration
        80,     # pit speed limit
        0,      # game paused
        0,      # is spectating
        0,      # spectator car index
        0,      # SLI Pro native support
        2,      # number of valid marshal zones
    )

    # All 21 marshal zone slots are always present
    for i in range(MAX_MARSHAL_ZONES):
        if i == 0:
            data += make_marshal_zone(
                zone_start=0.10,
                zone_flag=1,
            )
        elif i == 1:
            data += make_marshal_zone(
                zone_start=0.40,
                zone_flag=3,
            )
        else:
            data += make_marshal_zone(
                zone_start=0.0,
                zone_flag=-1,
            )

    # Fields between marshal zones and weather forecast samples
    data += struct.pack(
        "<BBB",
        0,      # safety car status
        0,      # network game
        2,      # number of valid weather forecast samples
    )

    # All 64 weather forecast slots are always present
    for i in range(MAX_WEATHER_FORECAST_SAMPLES):
        if i == 0:
            data += make_weather_sample(
                session_type=15,
                time_offset=0,
                weather=0,
            )
        elif i == 1:
            data += make_weather_sample(
                session_type=15,
                time_offset=5,
                weather=3,
            )
        else:
            data += make_weather_sample(
                session_type=0,
                time_offset=0,
                weather=0,
            )

    # Remaining session fields
    data += struct.pack(
        "<"
        "BB"
        "III"
        "3B"
        "9B"
        "BB"
        "I"
        "B"
        "4B"
        "3B"
        "24B"
        "B"
        "12B"
        "ff",

        0,          # forecast accuracy - perfect
        90,         # AI difficulty

        1001,       # season link identifier
        1002,       # weekend link identifier
        1003,       # session link identifier

        3,          # ideal pit lap
        4,          # latest pit lap
        2,          # predicted rejoin position

        # Assists / racing line
        0,          # steering assist
        0,          # braking assist
        1,          # gearbox assist
        0,          # pit assist
        0,          # pit release assist
        0,          # ERS assist
        0,          # DRS assist
        2,          # dynamic racing line
        0,          # dynamic racing line type

        4,          # game mode
        1,          # rule set

        840,        # time of day - 14:00

        3,          # session length

        1,          # lead player speed units - KPH
        0,          # lead player temperature - Celsius
        1,          # secondary player speed units - KPH
        0,          # secondary player temperature - Celsius

        0,          # number of safety car periods
        0,          # number of virtual safety car periods
        0,          # number of red flag periods

        # Simulation / rules settings (24 fields)
        0,          # equal car performance
        1,          # recovery mode
        3,          # flashback limit
        1,          # surface type
        0,          # low fuel mode
        0,          # race starts
        1,          # tyre temperature
        0,          # pit lane tyre sim
        3,          # car damage
        1,          # car damage rate
        2,          # collisions
        0,          # collisions off first lap only
        0,          # MP unsafe pit release
        0,          # MP off for griefing
        1,          # corner cutting stringency
        1,          # parc ferme rules
        2,          # pit stop experience
        2,          # safety car
        1,          # safety car experience
        1,          # formation lap
        1,          # formation lap experience
        2,          # red flags
        0,          # affects licence level solo
        0,          # affects licence level MP

        3,          # number of sessions in weekend

        # 12 reserved weekend structure entries
        1,          # practice 1
        5,          # qualifying 1
        15,         # race
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,

        2000.0,     # sector 2 start distance
        4000.0,     # sector 3 start distance
    )

    return data


# actual tests

def test_marshal_zone_size():
    assert MARSHAL_ZONE_SIZE == 5


def test_weather_forecast_size():
    assert WEATHER_FORECAST_SIZE == 8

def test_session_size():
    assert SESSION_SIZE == 724

def test_session_packet_size():
    assert SESSION_PACKET_SIZE == 753
    assert len(make_session_packet()) == SESSION_PACKET_SIZE


def test_marshal_zone_reads():
    data = make_marshal_zone(zone_start=0.35, zone_flag=3)

    zone = MarshalZone.from_bytes(data, 0)

    assert zone.zone_start == pytest.approx(0.35)
    assert zone.zone_flag == 3

def test_weather_forecast_reads():
    data = make_weather_sample(session_type=15, time_offset=10, weather=3)

    sample = WeatherForecastSample.from_bytes(data, 0)

    assert sample.session_type == 15
    assert sample.time_offset == 10
    assert sample.weather == 3

    assert sample.track_temperature == 25
    assert sample.track_temperature_change == 2

    assert sample.air_temperature == 18
    assert sample.air_temperature_change == 2

    assert sample.rain_percentage == 10   

def test_session_packet_reads():
    data = make_session_packet()

    packet = SessionPacket.from_bytes(data)

    assert packet.header.packet_id == PacketId.SESSION

    assert packet.weather == 0
    assert packet.track_temperature == 25
    assert packet.air_temperature == 18

    assert packet.total_laps == 5
    assert packet.track_length == 5891

    assert packet.session_type == 15
    assert packet.track_id == 7
    assert packet.formula == 0

    assert packet.session_time_left == 900
    assert packet.session_duration == 1200

    assert packet.pit_speed_limit == 80

    assert packet.game_paused == 0
    assert packet.is_spectating == 0

    # marshal zone stuff
    assert packet.num_marshal_zones == 2
    assert len(packet.marshal_zones) == 2

    assert packet.marshal_zones[0].zone_start == pytest.approx(0.10)
    assert packet.marshal_zones[0].zone_flag == 1

    assert packet.marshal_zones[1].zone_start == pytest.approx(0.40)
    assert packet.marshal_zones[1].zone_flag == 3

    assert packet.safety_car_status == 0
    assert packet.network_game == 0

    # weather forecast stuff
    assert packet.num_weather_forecast_samples == 2
    assert len(packet.weather_forecast_samples) == 2

    assert packet.weather_forecast_samples[0].time_offset == 0
    assert packet.weather_forecast_samples[0].weather == 0

    assert packet.weather_forecast_samples[1].time_offset == 5
    assert packet.weather_forecast_samples[1].weather == 3

    assert packet.forecast_accuracy == 0
    assert packet.ai_difficulty == 90

    # Identifiers
    assert packet.season_link_identifier == 1001
    assert packet.weekend_link_identifier == 1002
    assert packet.session_link_identifier == 1003

    # strategy
    assert packet.pit_stop_window_ideal_lap == 3
    assert packet.pit_stop_window_latest_lap == 4
    assert packet.pit_stop_rejoin_position == 2

    # session configuration
    assert packet.time_of_day == 840
    assert packet.session_length == 3

    assert packet.num_safety_car_periods == 0
    assert packet.num_virtual_safety_car_periods == 0
    assert packet.num_red_flag_periods == 0

    # weekend structure
    assert packet.num_sessions_in_weekend == 3

    assert packet.weekend_structure == (
        1,
        5,
        15,
    )

    # sector boundaries
    assert packet.sector2_lap_distance_start == pytest.approx(2000.0)
    assert packet.sector3_lap_distance_start == pytest.approx(4000.0)

def test_session_packet_rejects_wrong_size():
    with pytest.raises(ValueError):
        SessionPacket.from_bytes(bytes(100))