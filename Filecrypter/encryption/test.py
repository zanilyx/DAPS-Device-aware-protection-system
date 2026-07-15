import uuid
from pathlib import Path
print(str(uuid.getnode()))
import sqlite3

current_device = str(uuid.getnode())