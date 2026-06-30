import sqlite3
import socket
import uuid

def get_mac_address():
    mac = uuid.getnode()
    return ':'.join(
        f'{(mac >> ele) & 0xff:02x}'
        for ele in range(40, -1, -8)
    )

def get_local_ip():
    try:
        return socket.gethostbyname(socket.gethostname())
    except:
        return "Unknown"


conn = sqlite3.connect("devices.db")
cur = conn.cursor()

cur.execute("""
INSERT INTO devices
(
    device_id,
    device_type,
    hostname,
    mac_address,
    ip_address,
    owner
)
VALUES (?, ?, ?, ?, ?, ?)
""",
(
    str(uuid.getnode()),
    "Laptop",
    socket.gethostname(),
    get_mac_address(),
    get_local_ip(),
    "admin"
))

conn.commit()
conn.close()