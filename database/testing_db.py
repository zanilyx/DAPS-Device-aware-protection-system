import sqlite3
import uuid
from pathlib import Path
import sys

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from Filecrypter.encryption.encrypt import encrypt_file


DB_FILE = "files.db"


def add_encrypted_file(
    file_path,
    classification="Confidential",
    department="IT",
    role="Admin",
    access_type="Read/Write",
    owner="Ritesh"
):
    # Encrypt using your existing function
    encrypted_path = encrypt_file(file_path)

    file_id = str(uuid.uuid4())

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO files (
        file_id,
        filename,
        path,
        classification,
        department,
        role,
        access_type,
        encryption_status,
        owner
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        file_id,
        Path(encrypted_path).name,
        str(encrypted_path),
        classification,
        department,
        role,
        access_type,
        "Encrypted",
        owner
    ))

    conn.commit()
    conn.close()

    return file_id


# Example
if __name__ == "__main__":
    file_id = add_encrypted_file("test.txt")
    print("Stored:", file_id)