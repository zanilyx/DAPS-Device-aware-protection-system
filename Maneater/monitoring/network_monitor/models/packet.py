"""
packet.py

Represents one normalized packet after parsing.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Packet:

    timestamp: float

    src_ip: str
    dst_ip: str

    src_port: int
    dst_port: int

    protocol: str

    size: int

    direction: str

    interface: str

    process: Optional[str] = None