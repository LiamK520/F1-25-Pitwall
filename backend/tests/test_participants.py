import struct

import pytest

from udp.participants import NUM_CARS, PARTICIPANT_SIZE, PARTICIPANTS_PACKET_SIZE, ParticipantData, ParticipantsPacket


HEADER_FORMAT = "<HBBBBBQfIIBB"
PARTICIPANT_FORMAT = "<BBBBBBB32sBBHBB12B"


def make_header(packet_id: int) -> bytes:
    return struct.pack(
        HEADER_FORMAT,
        2025,       # packet_format
        25,         # game_year
        1,          # game_major_version
        0,          # game_minor_version
        1,          # packet_version
        packet_id,
        123456789,  # session_uid
        42.5,       # session_time
        100,        # frame_identifier
        100,        # overall_frame_identifier
        0,          # player_car_index
        255,        # secondary_player_car_index
    )


def make_participant(
    name: str = "Max Verstappen",
    driver_id: int = 9,
    team_id: int = 2,
    race_number: int = 1,
) -> bytes:
    encoded_name = name.encode("utf-8")

    # Participant names occupy exactly 32 bytes in the packet.
    encoded_name = encoded_name[:31] + b"\x00"
    encoded_name = encoded_name.ljust(32, b"\x00")

    return struct.pack(
        PARTICIPANT_FORMAT,
        0,               # ai_controlled
        driver_id,
        0,               # network_id
        team_id,
        0,               # my_team
        race_number,
        22,              # nationality - Dutch
        encoded_name,
        1,               # your_telemetry
        1,               # show_online_names
        0,               # tech_level
        1,               # platform - Steam
        2,               # num_colours

        # Four RGB colours
        255, 0, 0,
        0, 0, 255,
        0, 0, 0,
        0, 0, 0,
    )


def make_participants_packet(num_active_cars: int = 20) -> bytes:
    data = make_header(packet_id=4)

    data += struct.pack("<B", num_active_cars)

    for i in range(NUM_CARS):
        data += make_participant(
            name=f"Driver {i}",
            driver_id=i,
            team_id=i % 10,
            race_number=i + 1,
        )

    return data

def test_participant_size():
    assert PARTICIPANT_SIZE == 57

def test_participants_packet_size():
    assert PARTICIPANTS_PACKET_SIZE == 1284

def test_participant_data_read():
    data = make_participant(
        name="Max Verstappen",
        driver_id=9,
        team_id=2,
        race_number=1,
    )

    participant = ParticipantData.from_bytes(data, 0)

    assert participant.name == "Max Verstappen"
    assert participant.driver_id == 9
    assert participant.team_id == 2
    assert participant.race_number == 1
    assert participant.nationality == 22

    assert len(participant.livery_colours) == 2

    assert participant.livery_colours[0].red == 255
    assert participant.livery_colours[0].green == 0
    assert participant.livery_colours[0].blue == 0

    assert participant.livery_colours[1].red == 0
    assert participant.livery_colours[1].green == 0
    assert participant.livery_colours[1].blue == 255


def test_participants_packet_reads_all_cars():
    data = make_participants_packet(num_active_cars=20)

    packet = ParticipantsPacket.from_bytes(data)

    assert packet.header.packet_id == 4
    assert packet.num_active_cars == 20

    assert len(packet.participants) == 22

    assert packet.participants[0].name == "Driver 0"
    assert packet.participants[0].race_number == 1

    assert packet.participants[5].name == "Driver 5"
    assert packet.participants[5].race_number == 6

    assert packet.participants[21].name == "Driver 21"
    assert packet.participants[21].race_number == 22

def test_participants_packet_rejects_wrong_size():
    data = bytes(100)

    with pytest.raises(ValueError):
        ParticipantsPacket.from_bytes(data)