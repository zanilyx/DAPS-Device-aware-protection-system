"""
capture.py

Captures packets using Scapy (Npcap on Windows)
and updates statistics.py
"""

from threading import Thread

from scapy.all import sniff
from scapy.layers.inet import IP, TCP, UDP, ICMP

from ip_utils import is_local, is_loopback
from statistics import update


# -------------------------------------
# Capture Thread
# -------------------------------------

capture_thread = None
running = False


# -------------------------------------
# Packet Handler
# -------------------------------------

def process_packet(packet):

    if not packet.haslayer(IP):
        return

    ip = packet[IP]

    src = ip.src
    dst = ip.dst

    # Ignore localhost traffic
    if is_loopback(src) or is_loopback(dst):
        return

    packet_size = len(packet)

    protocol = "OTHER"
    port = 0

    # TCP
    if packet.haslayer(TCP):

        protocol = "TCP"

        tcp = packet[TCP]

        if is_local(src):
            port = tcp.dport
        else:
            port = tcp.sport

    # UDP
    elif packet.haslayer(UDP):

        protocol = "UDP"

        udp = packet[UDP]

        if is_local(src):
            port = udp.dport
        else:
            port = udp.sport

    # ICMP
    elif packet.haslayer(ICMP):

        protocol = "ICMP"

    # Outgoing
    if is_local(src):

        update(
            remote_ip=dst,
            direction="upload",
            byte_count=packet_size,
            protocol=protocol,
            port=port
        )

    # Incoming
    elif is_local(dst):

        update(
            remote_ip=src,
            direction="download",
            byte_count=packet_size,
            protocol=protocol,
            port=port
        )


# -------------------------------------
# Sniffer
# -------------------------------------

def capture_loop():

    global running

    running = True

    sniff(
        prn=process_packet,
        store=False
    )


# -------------------------------------
# Start
# -------------------------------------

def start_capture():

    global capture_thread

    capture_thread = Thread(
        target=capture_loop,
        daemon=True
    )

    capture_thread.start()


# -------------------------------------
# Stop
# -------------------------------------

def stop_capture():

    global running

    running = False