import socket

from udp.participants import ParticipantsPacket
from udp.decoder import decode_packet
from udp.motion import MotionPacket
from udp.lap_data import LapDataPacket

# maybe change to loopback later
UDP_IP = "0.0.0.0"
UDP_PORT = 20777
BUFFER_SIZE = 4096
# socket timeout as otherwise keyboard interrupt will be blocked if no packet received
# 0.5s will never cause issue in data flow as we receive packets at 20-60Hz
SOCKET_TIMEOUT = 0.5


def run_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(SOCKET_TIMEOUT)

    print(f"Listening for F1 25 UDP data on port {UDP_PORT}")

    while True:
        try:
            data, address = sock.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            continue

        try:
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

        except NotImplementedError:
            # Don't do anything for noww
            pass
        except ValueError as e:
            print(f"Error: Invalid packet from {address}: {e}")

if __name__ == "__main__":
    try:
        run_receiver()
    except KeyboardInterrupt:
        print("\nStopping UDP receiver")