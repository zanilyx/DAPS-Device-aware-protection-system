import uuid
import socket


def get_mac_address():
    mac = uuid.getnode()
    return ':'.join(f'{(mac >> ele) & 0xff:02x}'
                    for ele in range(40, -1, -8))


def get_local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "Unknown"