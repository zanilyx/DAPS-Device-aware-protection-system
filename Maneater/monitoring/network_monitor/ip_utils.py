import socket
import psutil


def get_local_ips():
    """
    Returns all IPv4 addresses assigned to this computer.
    """

    local_ips = set()

    interfaces = psutil.net_if_addrs()

    for interface in interfaces.values():

        for addr in interface:

            if addr.family == socket.AF_INET:
                local_ips.add(addr.address)

    return local_ips


LOCAL_IPS = get_local_ips()


def is_local(ip):

    return ip in LOCAL_IPS


def is_loopback(ip):

    return ip.startswith("127.")


def reverse_dns(ip):

    try:
        return socket.gethostbyaddr(ip)[0]

    except Exception:
        return "Unknown"