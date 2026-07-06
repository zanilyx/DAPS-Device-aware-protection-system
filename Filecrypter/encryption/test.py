import uuid
from pathlib import Path
print(uuid.getnode())
import sqlite3

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DEVICE = ROOT_DIR / "database" / "devices.db"
conn = sqlite3.connect(DEVICE)
cur = conn.cursor()

cur.execute("SELECT owner, device_id FROM devices")
print(cur.fetchall())