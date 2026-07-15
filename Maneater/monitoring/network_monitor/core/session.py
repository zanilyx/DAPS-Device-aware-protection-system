"""
session.py

Stores the entire monitoring session.

Total upload/download bytes come from psutil.net_io_counters(),
which reads directly from the NIC driver — the same source as
Task Manager. This is more accurate than summing IP-layer packet
sizes from Scapy, which misses Ethernet overhead, ACKs, and
retransmits.

Per-flow breakdowns still come from Scapy (flows.py) and are
best-effort, but session-level totals will now match what your
OS reports.
"""

from dataclasses import dataclass, field
from time import time
from typing import Dict

import psutil

from models.flow import Flow
from core.interface import get_capture_interface


def _get_iface_name():
    """
    Return the psutil interface name that matches the Scapy
    capture interface. psutil and Scapy may use slightly
    different naming on Windows (e.g. Scapy uses the NPF GUID,
    psutil uses the friendly name), so we match by the local IP.
    """

    try:
        from utils.ip_utils import LOCAL_IPS_V4
        addrs = psutil.net_if_addrs()

        for name, addr_list in addrs.items():
            for addr in addr_list:
                if addr.address in LOCAL_IPS_V4:
                    return name

    except Exception:
        pass

    return None


def _read_counters(iface_name):
    """
    Read bytes_sent / bytes_recv for a specific interface.
    Falls back to system-wide totals if the interface isn't found.
    """

    try:
        counters = psutil.net_io_counters(pernic=True)

        if iface_name and iface_name in counters:
            c = counters[iface_name]
            return c.bytes_sent, c.bytes_recv

        # Fallback: system-wide totals
        c = psutil.net_io_counters()
        return c.bytes_sent, c.bytes_recv

    except Exception:
        return 0, 0


@dataclass
class Session:

    start_time: float = field(default_factory=time)

    # Per-flow packet count (still from Scapy)
    total_packets: int = 0

    flows: Dict[tuple, Flow] = field(default_factory=dict)

    def __post_init__(self):

        self._iface_name        = _get_iface_name()
        self._baseline_upload   = 0
        self._baseline_download = 0

    def reset_baseline(self):
        """
        Snapshot the NIC counters right now.
        Call this at the exact moment capture starts — not at
        import time — so the baseline is as close as possible
        to t=0 of actual traffic capture and nothing gets missed.
        """

        sent, recv = _read_counters(self._iface_name)
        self._baseline_upload   = sent
        self._baseline_download = recv
        self.start_time         = time()

        print(
            f"Baseline snapshot: "
            f"iface={self._iface_name} "
            f"sent={sent} recv={recv}"
        )

    # --------------------------------------------------
    # Accurate totals from the NIC driver
    # --------------------------------------------------

    @property
    def total_upload(self):

        sent, _ = _read_counters(self._iface_name)
        return max(0, sent - self._baseline_upload)

    @property
    def total_download(self):

        _, recv = _read_counters(self._iface_name)
        return max(0, recv - self._baseline_download)

    # --------------------------------------------------
    # Packet counter (still Scapy-based, fine for counts)
    # --------------------------------------------------

    def add_upload(self, size: int):
        self.total_packets += 1

    def add_download(self, size: int):
        self.total_packets += 1

    # --------------------------------------------------
    # Derived properties
    # --------------------------------------------------

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