import socket
import threading

from udp.decoder import decode_packet
from udp.recorder import PacketRecorder

from state.application_state import ApplicationState

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


def run_receiver(state: ApplicationState, stop_event: threading.Event, record=False):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(SOCKET_TIMEOUT)

    recorder: PacketRecorder | None = None
    if record:
        recorder = PacketRecorder("recordings/test.bin")
        recorder.open()

    print(f"Listening for F1 25 UDP data on port {UDP_PORT}")

    try:
        while not stop_event.is_set():
            try:
                data, address = sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue

            try:
                if recorder is not None:
                    recorder.record_packet(data)
                packet = decode_packet(data)

                if packet is None:
                    # skip motion ex, lobby info and time trial packets
                    continue

                state.update(packet)

            except NotImplementedError:
                # Don't do anything for noww
                pass
            except ValueError as e:
                print(f"Error: Invalid packet from {address}: {e}")

    finally:
        print("Closing recorder and socket")
        sock.close()
        if recorder is not None:
            recorder.close()

if __name__ == "__main__":
    args = parse_args()
    state = ApplicationState()
    stop_event = threading.Event()

    try:
        run_receiver(state, stop_event, record=args.record)
    except KeyboardInterrupt:
        print("\nStopping UDP receiver")