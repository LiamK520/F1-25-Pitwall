import time
import struct
from pathlib import Path
import socket

# struct stores timestamp in ns and size of data recorded
RECORD_HEADER = struct.Struct("<QI")

# same as f1 25
HOST = "127.0.0.1"
PORT = 20777

# TODO: probably add some error handling to this class at some point
class PacketReplayer:

    def __init__(self, path):
        self.path = Path(path)
        self.fp = None
        self.sock = None


    def open(self):
        if self.fp: return

        self.fp = self.path.open("rb")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def close(self):
        if not self.fp: return

        self.fp.close()
        self.sock.close()
        self.fp = None
        self.sock = None

    def replay(self):
        if not self.fp or not self.sock: return

        start_time = time.monotonic_ns()

        while True:
            header = self.fp.read(RECORD_HEADER.size)

            if not header:
                break

            timestamp, packet_size = RECORD_HEADER.unpack(header)

            data = self.fp.read(packet_size)

            target = start_time + timestamp#

            while True:
                rem = target - time.monotonic_ns()

                if rem <= 0:
                    break

                # sleep for remainder in second
                time.sleep(rem / 1E9)

            self.sock.sendto(data, (HOST, PORT))

if __name__ == "__main__":
    replayer = PacketReplayer("recordings/test.bin")

    try:
        replayer.open()
        replayer.replay()
    finally:
        replayer.close()