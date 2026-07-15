"""
interface.py

Returns the Scapy/Npcap interface name (full NPF GUID on Windows)
for the adapter that carries the default route.

On Windows, Scapy needs the full GUID like:
    \\Device\\NPF_{7FCBC1AB-F312-43EB-B8D4-E40E936757D8}
NOT the friendly name like "Wi-Fi" -- using the friendly name
causes Scapy to silently capture on the wrong adapter or miss
most packets.
"""

import socket

from scapy.all import IFACES


def get_default_route_ip():
    """
    Ask the OS which local IP it would use to reach the internet.
    No packets are actually sent.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return None
    finally:
        s.close()


def get_capture_interface():

    default_ip = get_default_route_ip()

    # -------------------------------------------------------
    # Primary: match the Scapy interface whose IP matches the
    # default route IP. This returns the full NPF GUID which
    # Scapy/Npcap needs on Windows.
    # -------------------------------------------------------

    if default_ip:

        for name, iface in IFACES.items():

            ip = getattr(iface, "ip", None)

            if ip == default_ip:

                print(f"\nUsing interface: {name}")
                print(f"IP: {ip}\n")

                return name  # full NPF GUID e.g. \Device\NPF_{...}

    # -------------------------------------------------------
    # Fallback: any non-loopback interface with a real IP
    # -------------------------------------------------------

    for name, iface in IFACES.items():

        ip = getattr(iface, "ip", None)

        if ip and not ip.startswith("127.") and not ip.startswith("169.254."):

            print(f"\nFallback interface: {name}")
            print(f"IP: {ip}\n")

            return name

    raise RuntimeError("No suitable network interface found.")