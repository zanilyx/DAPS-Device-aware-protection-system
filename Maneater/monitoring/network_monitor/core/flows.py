"""
flows.py

Maintains all active network flows.
"""

from threading import Lock

from models.flow import Flow
from models.session import Session

from utils.config import (
    WHITELIST,
    BLACKLIST
)

# -------------------------------------------------
# Global Session
# -------------------------------------------------

SESSION = Session()

lock = Lock()


# -------------------------------------------------
# Flow Key
# -------------------------------------------------

def create_flow_key(packet):
    """
    Make both directions of a TCP/UDP conversation
    map to the same Flow.
    """

    endpoints = sorted([
        (packet.src_ip, packet.src_port),
        (packet.dst_ip, packet.dst_port)
    ])

    return (
        endpoints[0],
        endpoints[1],
        packet.protocol
    )


# -------------------------------------------------
# Status
# -------------------------------------------------

def get_status(packet):

    if packet.src_ip in BLACKLIST:
        return "BLACKLIST"

    if packet.dst_ip in BLACKLIST:
        return "BLACKLIST"

    if packet.src_ip in WHITELIST:
        return "WHITELIST"

    if packet.dst_ip in WHITELIST:
        return "WHITELIST"

    return "UNKNOWN"


# -------------------------------------------------
# Create Flow
# -------------------------------------------------

def create_flow(packet):

    flow = Flow(

        src_ip=packet.src_ip,

        dst_ip=packet.dst_ip,

        src_port=packet.src_port,

        dst_port=packet.dst_port,

        protocol=packet.protocol

    )

    flow.status = get_status(packet)

    return flow


# -------------------------------------------------
# Process Packet
# -------------------------------------------------

def process_packet(packet):

    key = create_flow_key(packet)

    with lock:

        if key not in SESSION.flows:

            SESSION.flows[key] = create_flow(packet)

        flow = SESSION.flows[key]

        if packet.direction == "upload":

            flow.update_upload(packet.size)

            SESSION.add_upload(packet.size)

        else:

            flow.update_download(packet.size)

            SESSION.add_download(packet.size)


# -------------------------------------------------
# Session Snapshot
# -------------------------------------------------

def get_session():

    with lock:

        return SESSION


# -------------------------------------------------
# Top Uploads
# -------------------------------------------------

def top_uploads(limit=10):

    with lock:

        return sorted(

            SESSION.flows.values(),

            key=lambda f: f.upload_bytes,

            reverse=True

        )[:limit]


# -------------------------------------------------
# Top Downloads
# -------------------------------------------------

def top_downloads(limit=10):

    with lock:

        return sorted(

            SESSION.flows.values(),

            key=lambda f: f.download_bytes,

            reverse=True

        )[:limit]


# -------------------------------------------------
# Top Flows (by total traffic, upload + download)
# -------------------------------------------------

def top_flows(limit=100):

    with lock:

        return sorted(

            SESSION.flows.values(),

            key=lambda f: f.total_bytes,

            reverse=True

        )[:limit]


# -------------------------------------------------
# Active Flow Count
# -------------------------------------------------

def active_flows():

    with lock:

        return len(SESSION.flows)