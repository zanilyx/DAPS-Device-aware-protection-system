import os
import sys
import sqlite3
import uuid
import socket
from datetime import datetime
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog
from Crypto.Cipher import AES


ROOT_DIR = Path(__file__).resolve().parent.parent.parent

USERS_DB   = ROOT_DIR / "database" / "users.db"
DEVICES_DB = ROOT_DIR / "database" / "devices.db"
FILES_DB   = ROOT_DIR / "database" / "files.db"
LOGS_DB    = ROOT_DIR / "database" / "logs.db"



# ==================================================
# CONFIG
# ==================================================

CURRENT_USER = "admin"      # Replace with login username


# ==================================================
# AES KEY
# ==================================================

def get_aes_key():
    secret_input = "my_super_secret_key_password_123"
    return secret_input.ljust(32, '0')[:32].encode('utf-8')


# ==================================================
# DEVICE INFO
# ==================================================

def get_device_id():
    return str(uuid.getnode())


def get_hostname():
    return socket.gethostname()


# ==================================================
# AUDIT LOGGING
# ==================================================

def log_event(
        username,
        file_id,
        action,
        status,
        details=""):

    conn = sqlite3.connect(LOGS_DB)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO logs
        (
            timestamp,
            username,
            file_id,
            action,
            status,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            username,
            file_id,
            action,
            status,
            details
        )
    )

    conn.commit()
    conn.close()


# ==================================================
# USER ROLE
# ==================================================

def get_user_role(username):

    conn = sqlite3.connect(USERS_DB)
    cur = conn.cursor()

    cur.execute(
        "SELECT role FROM users WHERE username=?",
        (username,)
    )

    row = cur.fetchone()

    conn.close()

    return row[0] if row else None


# ==================================================
# DEVICE CHECK
# ==================================================

def verify_device(username):

    device_id = str(uuid.getnode())

    conn = sqlite3.connect(DEVICES_DB)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT device_id
        FROM devices
        WHERE username=?
        """,
        (username,)
    )

    row = cur.fetchone()

    conn.close()

    return bool(row and row[0] == device_id)


# ==================================================
# FILE ACCESS CHECK
# ==================================================

def can_access_file(file_id, role):

    conn = sqlite3.connect(FILES_DB)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT role_name
        FROM files
        WHERE file_id=?
        """,
        (file_id,)
    )

    roles = [r[0] for r in cur.fetchall()]

    conn.close()

    return role in roles


# ==================================================
# GET FILE ID
# ==================================================

def get_file_id(filename):

    conn = sqlite3.connect(FILES_DB)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id
        FROM files
        WHERE encrypted_name=?
        """,
        (filename,)
    )

    row = cur.fetchone()

    conn.close()

    return row[0] if row else None


# ==================================================
# MAIN DECRYPTION
# ==================================================

def decrypt_file(file_path=None):

    if not file_path:

        app = QApplication.instance() or QApplication(sys.argv)

        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select File to Decrypt",
            "",
            "TVK Files (*.tvk)"
        )

        if not file_path:
            return None

    try:

        # -----------------------------------
        # Get File ID
        # -----------------------------------

        file_name = os.path.basename(file_path)

        file_id = get_file_id(file_name)

        if not file_id:

            print("File not registered in database.")

            log_event(
                CURRENT_USER,
                0,
                "DECRYPT",
                "FAILED",
                "Unknown File"
            )

            return None

        # -----------------------------------
        # User Role Check
        # -----------------------------------

        user_role = get_user_role(CURRENT_USER)

        if not user_role:

            print("User not found.")

            log_event(
                CURRENT_USER,
                file_id,
                "DECRYPT",
                "FAILED",
                "User Not Found"
            )

            return None

        # -----------------------------------
        # Device Check
        # -----------------------------------

        if not verify_device(CURRENT_USER):

            print("Access Denied: Unregistered Device")

            log_event(
                CURRENT_USER,
                file_id,
                "DECRYPT",
                "DENIED",
                "Invalid Device"
            )

            return None

        # -----------------------------------
        # Role Check
        # -----------------------------------

        if not can_access_file(file_id, user_role):

            print("Access Denied: Role Not Authorized")

            log_event(
                CURRENT_USER,
                file_id,
                "DECRYPT",
                "DENIED",
                f"Role={user_role}"
            )

            return None

        # -----------------------------------
        # AES Decryption
        # -----------------------------------

        key = get_aes_key()

        with open(file_path, "rb") as f:

            ext_encoded = f.read(16)
            nonce = f.read(16)
            tag = f.read(16)
            ciphertext = f.read()

        original_extension = (
            ext_encoded
            .decode("utf-8")
            .rstrip("\x00")
        )

        cipher = AES.new(
            key,
            AES.MODE_GCM,
            nonce=nonce
        )

        decrypted_data = cipher.decrypt_and_verify(
            ciphertext,
            tag
        )

        output_path = (
            os.path.splitext(file_path)[0]
            + original_extension
        )

        with open(output_path, "wb") as f:
            f.write(decrypted_data)

        print("Decryption Successful")

        log_event(
            CURRENT_USER,
            file_id,
            "DECRYPT",
            "SUCCESS",
            f"Role={user_role}"
        )

        return output_path

    except Exception as e:

        print(f"Decryption Error: {e}")

        log_event(
            CURRENT_USER,
            0,
            "DECRYPT",
            "FAILED",
            str(e)
        )

        return None


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":

    path_arg = sys.argv[1] if len(sys.argv) > 1 else None

    result = decrypt_file(path_arg)

    if result:
        print(f"Recovered File: {result}")