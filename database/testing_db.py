import sqlite3
from pathlib import Path

# ==========================================================
# DATABASE PATH
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

DB = ROOT_DIR / "database" / "devices.db"

# ==========================================================
# CONNECT
# ==========================================================

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ==========================================================
# CREATE USB TABLE
# ==========================================================

cur.execute("""

CREATE TABLE IF NOT EXISTS usb_devices (

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    device_id TEXT UNIQUE NOT NULL,

    manufacturer TEXT NOT NULL,

    device_name TEXT NOT NULL,

    model TEXT NOT NULL,

    pnp_device_id TEXT NOT NULL,

    owner TEXT NOT NULL,

    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)

""")

# ==========================================================
# INSERT TEST DEVICE
# ==========================================================

cur.execute("""

INSERT OR IGNORE INTO usb_devices
(
    device_id,
    manufacturer,
    device_name,
    model,
    pnp_device_id,
    owner
)

VALUES
(
    ?, ?, ?, ?, ?, ?
)

""",
(
    "4351a99ac85ede2b15ef9e98bb0138e7da3b989f381f2e26641ff41d9d9f1066",
    "(Standard disk drives)",
    "EVM EXTE RNAL SSD 256 SCSI Disk Device",
    "EVM EXTE RNAL SSD 256 SCSI Disk Device",
    r"SCSI\DISK&VEN_EVM_EXTE&PROD_RNAL_SSD_256\6&530062A&1&000000",
    "Piyush"
))

conn.commit()

print("usb_devices table created successfully.\n")

print("Contents of usb_devices:\n")

cur.execute("SELECT * FROM usb_devices")

for row in cur.fetchall():
    print(row)

conn.close()