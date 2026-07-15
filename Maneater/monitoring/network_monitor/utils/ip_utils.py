"""
ip_utils.py

Network helper functions.
"""

import socket
import psutil

LOCAL_IPS_V4 = set()
LOCAL_IPS_V6 = set()


def refresh_local_ips():

    LOCAL_IPS_V4.clear()
    LOCAL_IPS_V6.clear()

    interfaces = psutil.net_if_addrs()

    for addresses in interfaces.values():

        for addr in addresses:

            if addr.family == socket.AF_INET:
                LOCAL_IPS_V4.add(addr.address)

            elif addr.family == socket.AF_INET6:
                # Strip scope ID (e.g. %eth0) and normalise
                ip = addr.address.split("%")[0].lower()
                LOCAL_IPS_V6.add(ip)


refresh_local_ips()


def is_local(ip):
    # Normalise IPv6 for comparison
    return ip in LOCAL_IPS_V4 or ip.lower() in LOCAL_IPS_V6


def is_loopback(ip):
    return (
        ip.startswith("127.")
        or ip == "::1"
        or ip.lower() == "::1"
    )


def resolve_hostname(ip):

    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""