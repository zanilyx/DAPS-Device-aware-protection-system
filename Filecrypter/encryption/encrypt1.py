import os
import sys
import uuid
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog
from Crypto.Cipher import AES
import sqlite3
import base64
from .key import build_metadata, generate_key
from .decrypt import log_event
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

USERS_DB   = ROOT_DIR / "database" / "users.db"
DEVICES_DB = ROOT_DIR / "database" / "devices.db"
FILES_DB   = ROOT_DIR / "database" / "files.db"
KEYS_DB    = ROOT_DIR / "database" / "keys.db"
from GUI_modules.role_dialog import RoleSelectionDialog
COMPANY_DB = r"C:\Piyush\Projects\CCNCS\Files\code\Company DB"

def generate_aes_key():

    metadata = build_metadata()

    key = generate_key(metadata)

    return key

def save_key(file_id, key):

    encoded_key = base64.b64encode(key).decode()

    conn = sqlite3.connect(KEYS_DB)

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO keys
        (
            file_id,
            aes_key
        )
        VALUES (?, ?)
    """,
    (
        file_id,
        encoded_key
    ))

    conn.commit()
    conn.close()

def get_user_details(username):

    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT department, role
        FROM users
        WHERE username = ?
    """, (username,))

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0], row[1]

    return None, None

def encrypt_file(username, file_path=None):

    if not file_path:
        app = QApplication.instance() or QApplication(sys.argv)
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select File to Encrypt",
            ""
        )

        if not file_path:
            return None

    try:

        # -----------------------------------------
        # Generate File ID & AES Key
        # -----------------------------------------

        file_id = str(uuid.uuid4())
        department, role = get_user_details(username)

        if department is None:
            print("User not found in users.db")
            return None
        key = generate_aes_key()

        # Store key in keys.db
        save_key(file_id, key)

        # -----------------------------------------
        # Read file
        # -----------------------------------------

        filename = os.path.basename(file_path)

        _, ext = os.path.splitext(filename)

        ext_encoded = ext.encode("utf-8").ljust(16, b"\x00")

        with open(file_path, "rb") as f:
            data = f.read()

        # -----------------------------------------
        # Encrypt
        # -----------------------------------------

        cipher = AES.new(key, AES.MODE_GCM)

        ciphertext, tag = cipher.encrypt_and_digest(data)

        output_path = os.path.splitext(file_path)[0] + ".tvk"

        with open(output_path, "wb") as f:

            f.write(ext_encoded)
            f.write(cipher.nonce)
            f.write(tag)
            f.write(ciphertext)

        # -----------------------------------------
        # Save metadata in files.db
        # -----------------------------------------


        conn = sqlite3.connect(FILES_DB)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO files
        (
            file_id,
            filename,
            path,
            classification,
            department,
            role,
            access_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            file_id,
            os.path.basename(output_path),
            output_path,
            "Confidential",
            department,
            role,
            "Read/Write"
        ))

        conn.commit()
        conn.close()

        # -----------------------------------------
        # Audit Log
        # -----------------------------------------

        log_event(
            username,
            file_id,
            "ENCRYPT_SUCCESS",
            "File encrypted successfully"
        )

        return output_path

    except Exception as e:

        print(f"Encryption error: {e}")

        log_event(
            username,
            file_id if "file_id" in locals() else "UNKNOWN",
            "ENCRYPT_FAILED",
            str(e)
        )

        return None
if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = encrypt_file(path_arg)
    if result:
        print(f"Successfully encrypted to: {result}")