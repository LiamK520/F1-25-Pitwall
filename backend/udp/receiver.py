import socket

from udp.car_damage import CarDamagePacket
from udp.participants import ParticipantsPacket
from udp.decoder import decode_packet
from udp.motion import MotionPacket
from udp.lap_data import LapDataPacket
from udp.car_telemetry import CarTelemetryPacket
from udp.car_status import CarStatusPacket
from udp.session import SessionPacket

from udp.recorder import PacketRecorder

import argparse

# maybe change to loopback later
UDP_IP = "0.0.0.0"
UDP_PORT = 20777
BUFFER_SIZE = 4096
# socket timeout as otherwise keyboard interrupt will be blocked if no packet received
# 0.5s will never cause issue in data flow as we receive packets at 20-60Hz
SOCKET_TIMEOUT = 0.5

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--record", action="store_true", help="record incoming packets to file")

    return parser.parse_args()


def run_receiver(record=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(SOCKET_TIMEOUT)

    recorder = PacketRecorder("recordings/test.bin")
    if record:
        recorder.open()

    print(f"Listening for F1 25 UDP data on port {UDP_PORT}")

    try:
        while True:
            try:
                data, address = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue

            try:
                if record:
                    recorder.record_packet(data)
                packet = decode_packet(data)

                if isinstance(packet, MotionPacket):
                    # print player's position
                    player_index = packet.header.player_car_index
                    player = packet.cars[player_index]

                    print(
                        f"Car {player_index}: "
                        f"x={player.world_position_x:.2f}, "
                        f"y={player.world_position_y:.2f}, "
                        f"z={player.world_position_z:.2f}"
                    )

                if isinstance(packet, SessionPacket):
                    print(
                        f"Session type {packet.session_type} | "
                        f"Track {packet.track_id} | "
                        f"{packet.track_length}m | "
                        f"Weather {packet.weather} | "
                        f"SC {packet.safety_car_status} | "
                        f"Marshal zones {packet.num_marshal_zones} | "
                        f"Forecast samples {packet.num_weather_forecast_samples}"
                    )

                if isinstance(packet, LapDataPacket):
                    player_index = packet.header.player_car_index
                    player_lap = packet.cars[player_index]

                    print(
                        f"Car {player_index}: "
                        f"P{player_lap.car_position} | "
                        f"Lap {player_lap.current_lap_num} | "
                        f"Sector {player_lap.sector + 1} | "
                        f"{player_lap.lap_distance:.1f}m"
                    )

                if isinstance(packet, ParticipantsPacket):
                    print(f"Active cars: {packet.num_active_cars}")

                    for index, participant in enumerate(
                        packet.participants[:packet.num_active_cars]
                    ):
                        print(
                            f"{index:2}: "
                            f"{participant.name} "
                            f"(team={participant.team_id}, "
                            f"number={participant.race_number})"
                        )

                if isinstance(packet, CarTelemetryPacket):
                    player_index = packet.header.player_car_index
                    # using car - 1 as my recording used keyboard so not very interesting telemetry...
                    # car in recording is 19, be wary of error if rerunning and car index may be 0...
                    telem = packet.cars[player_index - 1]

                    print(
                        f"Car {player_index - 1}: "
                        f"{telem.speed} km/h | "
                        f"Throttle {telem.throttle:.2f} | "
                        f"Brake {telem.brake:.2f} | "
                        f"Gear {telem.gear} | "
                        f"RPM {telem.engine_rpm}"
                    )

                if isinstance(packet, CarStatusPacket):
                    player_index = packet.header.player_car_index
                    status = packet.cars[player_index]

                    print(
                        f"Car {player_index}: "
                        f"Fuel {status.fuel_in_tank:.1f}kg | "
                        f"Fuel laps {status.fuel_remaining_laps:.1f} | "
                        f"Tyre age {status.tyres_age_laps} | "
                        f"ERS {status.ers_store_energy / 1_000_000:.2f}MJ | "
                        f"DRS allowed {status.drs_allowed}"
                    )

                if isinstance(packet, CarDamagePacket):
                    player_index = packet.header.player_car_index
                    damage = packet.cars[player_index]

                    print(
                        f"Car {player_index}: "
                        f"Tyre wear {damage.tyres_wear} | "
                        f"Front lef wing {damage.front_left_wing_damage}% | "
                        f"Front right wing {damage.front_right_wing_damage}% | "
                        f"Floor {damage.floor_damage}% | "
                        f"Engine {damage.engine_damage}%"
                    )

            except NotImplementedError:
                # Don't do anything for noww
                pass
            except ValueError as e:
                print(f"Error: Invalid packet from {address}: {e}")

    finally:
        print("Closing recorder and socket")
        sock.close()
        recorder.close()

if __name__ == "__main__":
    args = parse_args()

    try:
        run_receiver(record=args.record)
    except KeyboardInterrupt:
        print("\nStopping UDP receiver")