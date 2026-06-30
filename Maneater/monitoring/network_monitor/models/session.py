"""
session.py

Stores the entire monitoring session.
"""

from dataclasses import dataclass, field
from time import time
from typing import Dict

from models.flow import Flow


@dataclass
class Session:

    start_time: float = field(default_factory=time)

    total_upload: int = 0
    total_download: int = 0

    total_packets: int = 0

    flows: Dict[tuple, Flow] = field(default_factory=dict)

    def add_upload(self, size: int):

        self.total_upload += size
        self.total_packets += 1

    def add_download(self, size: int):

        self.total_download += size
        self.total_packets += 1

    @property
    def runtime(self):

        return int(time() - self.start_time)
    
    @property
    def unique_ips(self):

        ips = set()

        for flow in self.flows.values():

            ips.add(flow.src_ip)
            ips.add(flow.dst_ip)

        return len(ips)


    @property
    def total_flows(self):

        return len(self.flows)