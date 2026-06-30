"""
statistics.py

Stores live traffic statistics for every remote IP.
Thread-safe.
"""

from collections import defaultdict
from threading import Lock
from time import time

from config import WHITELIST, BLACKLIST

# ---------------------------------------------------
# Thread Lock
# ---------------------------------------------------

lock = Lock()

# ---------------------------------------------------
# Session Information
# ---------------------------------------------------

SESSION_START = time()

TOTAL_UPLOAD = 0
TOTAL_DOWNLOAD = 0

TOTAL_PACKETS = 0

# Previous values for speed calculation
_last_upload = 0
_last_download = 0
_last_time = time()

UPLOAD_SPEED = 0
DOWNLOAD_SPEED = 0

# ---------------------------------------------------
# Per-IP Statistics
# ---------------------------------------------------

traffic = defaultdict(lambda: {

    "upload": 0,
    "download": 0,

    "packets": 0,

    "first_seen": time(),
    "last_seen": time(),

    "ports": set(),
    "protocols": set(),

    "status": "UNKNOWN"
})

# ---------------------------------------------------
# Status
# ---------------------------------------------------

def get_status(ip):

    if ip in WHITELIST:
        return "WHITELIST"

    if ip in BLACKLIST:
        return "BLACKLIST"

    return "UNKNOWN"

# ---------------------------------------------------
# Update Traffic
# ---------------------------------------------------

def update(remote_ip,
           direction,
           byte_count,
           protocol,
           port):

    global TOTAL_UPLOAD
    global TOTAL_DOWNLOAD
    global TOTAL_PACKETS

    with lock:

        entry = traffic[remote_ip]

        if direction == "upload":
            entry["upload"] += byte_count
            TOTAL_UPLOAD += byte_count

        else:
            entry["download"] += byte_count
            TOTAL_DOWNLOAD += byte_count

        entry["packets"] += 1
        TOTAL_PACKETS += 1

        entry["ports"].add(port)
        entry["protocols"].add(protocol)

        entry["last_seen"] = time()
        entry["status"] = get_status(remote_ip)

# ---------------------------------------------------
# Speeds
# ---------------------------------------------------

def calculate_speeds():

    global _last_upload
    global _last_download
    global _last_time

    global UPLOAD_SPEED
    global DOWNLOAD_SPEED

    now = time()

    elapsed = now - _last_time

    if elapsed <= 0:
        return

    with lock:

        UPLOAD_SPEED = (TOTAL_UPLOAD - _last_upload) / elapsed
        DOWNLOAD_SPEED = (TOTAL_DOWNLOAD - _last_download) / elapsed

        _last_upload = TOTAL_UPLOAD
        _last_download = TOTAL_DOWNLOAD

    _last_time = now

# ---------------------------------------------------
# Snapshot
# ---------------------------------------------------

def snapshot():

    with lock:

        return {

            "session_time": int(time() - SESSION_START),

            "total_upload": TOTAL_UPLOAD,

            "total_download": TOTAL_DOWNLOAD,

            "upload_speed": UPLOAD_SPEED,

            "download_speed": DOWNLOAD_SPEED,

            "total_packets": TOTAL_PACKETS,

            "unique_ips": len(traffic),

            "traffic": dict(traffic)

        }

# ---------------------------------------------------
# Human Readable Size
# ---------------------------------------------------

def format_bytes(num):

    units = [

        "B",
        "KB",
        "MB",
        "GB",
        "TB"

    ]

    value = float(num)

    for unit in units:

        if value < 1024:
            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} PB"