"""
parser.py

Converts Scapy packets into Packet objects.
"""

import time

from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.inet6 import IPv6

from models.packet import Packet

from utils.ip_utils import (
    is_local,
    is_loopback
)

from utils.config import SETTINGS

from core.flows import process_packet


def parse_packet(pkt):

    # -----------------------------
    # IPv4
    # -----------------------------

    if pkt.haslayer(IP):

        ip = pkt[IP]

        src = ip.src
        dst = ip.dst

        size = ip.len

    # -----------------------------
    # IPv6
    # -----------------------------

    elif pkt.haslayer(IPv6):

        ip = pkt[IPv6]

        src = ip.src
        dst = ip.dst

        # IPv6 payload length + 40-byte header
        size = ip.plen + 40

    else:

        return None

    # -----------------------------

    if SETTINGS["ignore_loopback"]:

        if is_loopback(src) or is_loopback(dst):
            return None

    protocol = "OTHER"

    src_port = 0
    dst_port = 0

    # -----------------------------
    # TCP
    # -----------------------------

    if pkt.haslayer(TCP):

        tcp = pkt[TCP]

        protocol = "TCP"

        src_port = tcp.sport
        dst_port = tcp.dport

    # -----------------------------
    # UDP
    # -----------------------------

    elif pkt.haslayer(UDP):

        udp = pkt[UDP]

        protocol = "UDP"

        src_port = udp.sport
        dst_port = udp.dport

    # -----------------------------
    # ICMP
    # -----------------------------

    elif pkt.haslayer(ICMP):

        protocol = "ICMP"

    # -----------------------------

    if is_local(src):

        direction = "upload"

    elif is_local(dst):

        direction = "download"

    else:

        # Not our traffic
        return None

    packet = Packet(

        timestamp=time.time(),

        src_ip=src,

        dst_ip=dst,

        src_port=src_port,

        dst_port=dst_port,

        protocol=protocol,

        size=size,

        direction=direction,

        interface=getattr(pkt, "sniffed_on", "")

    )

    process_packet(packet)

    return packet