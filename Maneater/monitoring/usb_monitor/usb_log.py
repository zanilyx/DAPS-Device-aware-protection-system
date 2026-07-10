import sqlite3
import getpass
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOGS_DB = ROOT_DIR / "database" / "logs.db"


def log_event(device_id: str, usb_type: str, action: str, status: str):
    """
    device_id : the sha256 device hash (same value used in usb_devices.device_id)
    usb_type  : short description, e.g. device_name or media_type
    action    : DEVICE_DETECTED / EJECT_ATTEMPT / DEVICE_DISABLED / MONITOR_ERROR etc.
    status    : SUCCESS / FAILED / AUTHORIZED / UNAUTHORIZED
    """
    conn = sqlite3.connect(LOGS_DB)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO usb_logs (device_id, timestamp, username, USB_Type, action, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            device_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            getpass.getuser(),
            usb_type,
            action,
            status,
        ))
        conn.commit()
    finally:
        conn.close()