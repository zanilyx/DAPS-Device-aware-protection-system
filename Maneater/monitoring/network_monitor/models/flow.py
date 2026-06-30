"""
flow.py

Represents one network flow.
"""

from dataclasses import dataclass, field
from time import time


@dataclass
class Flow:

    src_ip: str
    dst_ip: str

    src_port: int
    dst_port: int

    protocol: str

    upload_bytes: int = 0
    download_bytes: int = 0

    upload_packets: int = 0
    download_packets: int = 0

    first_seen: float = field(default_factory=time)
    last_seen: float = field(default_factory=time)

    process_name: str = ""

    hostname: str = ""

    status: str = "UNKNOWN"

    def update_upload(self, size: int):

        self.upload_bytes += size
        self.upload_packets += 1
        self.last_seen = time()

    def update_download(self, size: int):

        self.download_bytes += size
        self.download_packets += 1
        self.last_seen = time()

    @property
    def total_bytes(self):

        return self.upload_bytes + self.download_bytes

    @property
    def total_packets(self):

        return self.upload_packets + self.download_packets