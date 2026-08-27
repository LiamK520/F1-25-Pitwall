import time
import struct
from pathlib import Path

# struct stores timestamp in ns and size of data recorded
RECORD_HEADER = struct.Struct("<QI")

# TODO: probably add some error handling to this class at some point
class PacketRecorder:

    def __init__(self, path):
        self.start_time = None
        self.path = Path(path)
        self.fp = None

        self.path.parent.mkdir(parents=True, exist_ok=True)


    def open(self):
        if self.fp: return

        self.fp = self.path.open("wb")

    def close(self):
        if not self.fp: return

        self.fp.close()
        self.fp = None
        self.start_time = None

    # TODO: this is probably affected by in-game pausing which probably isn't good. change to use session time or something
    def record_packet(self, data: bytes):
        if not self.fp: return

        time_now = time.monotonic_ns()

        # zero time here as it takes me time to open f1 25 and start playing
        if self.start_time is None:
            self.start_time = time_now

        timestamp = time_now - self.start_time

        # encode timestamp and length of data in binary
        self.fp.write(RECORD_HEADER.pack(
            timestamp, len(data)
        ))

        self.fp.write(data)