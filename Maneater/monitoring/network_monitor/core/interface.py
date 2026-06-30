import socket

from scapy.all import IFACES
from utils.ip_utils import LOCAL_IPS_V4


def get_default_route_ip():
    """
    Find the local IP address actually used to reach the internet,
    i.e. the IP bound to whatever interface holds the default route.

    This doesn't send any real traffic -- UDP sockets don't connect
    until you send data, this just asks the OS to pick the route.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]

    except Exception:
        ip = None

    finally:
        s.close()

    return ip


def get_capture_interface():

    default_ip = get_default_route_ip()

    # ---------------------------------------------
    # Preferred: match the interface that owns the
    # IP used for the default route. This avoids
    # accidentally picking a VPN/virtual/secondary
    # adapter that only sees stray broadcast traffic.
    # ---------------------------------------------

    if default_ip:

        for iface in IFACES.values():

            ip = getattr(iface, "ip", None)

            if ip == default_ip:

                print(f"\nUsing interface (default route): {iface.name}")
                print(f"IP: {ip}\n")

                return iface.name

        print(
            f"\nWarning: default route IP {default_ip} did not match "
            f"any Scapy interface. Falling back to IP-list match.\n"
        )

    # ---------------------------------------------
    # Fallback: any interface whose IP we know about
    # (original behavior, kept as a backup)
    # ---------------------------------------------

    for iface in IFACES.values():

        ip = getattr(iface, "ip", None)

        if ip and ip in LOCAL_IPS_V4:

            print(f"\nUsing interface (IP list match): {iface.name}")
            print(f"IP: {ip}\n")

            return iface.name

    # ---------------------------------------------
    # Last resort: first non-loopback interface with
    # an IP at all
    # ---------------------------------------------

    for iface in IFACES.values():

        ip = getattr(iface, "ip", None)

        if ip and ip != "127.0.0.1":

            print(f"\nFallback interface: {iface.name}")
            print(f"IP: {ip}\n")

            return iface.name

    raise RuntimeError("No suitable interface found.")