import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent / "devices.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()



device_string = "0781|5581|SanDisk|USB123456789"
device_hash = hashlib.sha256(device_string.encode()).hexdigest()

# Insert test record
cursor.execute("""
INSERT OR IGNORE INTO usb_devices (
    serial_number,
    vid,
    pid,
    manufacturer,
    device_name,
    owner
)
VALUES (?, ?, ?, ?, ?, ?)
""", (
    device_hash,
    "0781",
    "5581",
    "SanDisk",
    "SanDisk Ultra USB 3.0",
    "Piyush"
))

conn.commit()
conn.close()

print("Table created and hashed test USB inserted.")