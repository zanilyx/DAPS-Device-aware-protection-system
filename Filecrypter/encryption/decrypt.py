import os
import sys
import json
import winreg
import socket
import sqlite3
import base64

from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox
)

from Crypto.Cipher import AES


# ==================================================
# DATABASE PATHS
# ==================================================

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

USERS_DB = ROOT_DIR / "database" / "users.db"
DEVICES_DB = ROOT_DIR / "database" / "devices.db"
FILES_DB = ROOT_DIR / "database" / "files.db"
LOGS_DB = ROOT_DIR / "database" / "logs.db"
KEYS_DB = ROOT_DIR / "database" / "keys.db"


# ==================================================
# AES KEY
# ==================================================

def get_aes_key(file_id):

    conn = sqlite3.connect(KEYS_DB)

    cur = conn.cursor()

    cur.execute("""
        SELECT aes_key
        FROM keys
        WHERE file_id=?
    """, (file_id,))

    row = cur.fetchone()

    if not row:

        conn.close()
        return None

    cur.execute("""
        UPDATE keys
        SET last_accessed=CURRENT_TIMESTAMP
        WHERE file_id=?
    """, (file_id,))

    conn.commit()

    conn.close()

    return base64.b64decode(row[0])


# ==================================================
# DEVICE INFO
# ==================================================

def get_device_id():

    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography"
        )

        machine_guid = winreg.QueryValueEx(
            key,
            "MachineGuid"
        )[0]

        winreg.CloseKey(key)

        return str(machine_guid)

    except Exception:
        return None


def get_hostname():

    return socket.gethostname()


# ==================================================
# AUDIT LOG
# ==================================================

def log_event(
        username,
        file_id,
        action,
        details=""):

    conn = sqlite3.connect(LOGS_DB)

    cur = conn.cursor()

    cur.execute("""
        INSERT INTO audit_logs
        (
            timestamp,
            username,
            device_id,
            file_id,
            action,
            details
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """,
    (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        username,
        get_device_id(),
        file_id,
        action,
        details
    ))

    conn.commit()
    conn.close()


# ==================================================
# USER ROLE
# ==================================================

def get_user_role(username):

    conn = sqlite3.connect(USERS_DB)

    cur = conn.cursor()

    cur.execute("""
        SELECT role
        FROM users
        WHERE username=?
    """, (username,))

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return None


# ==================================================
# DEVICE VERIFICATION
# ==================================================

def verify_device(username):

    current_device = get_device_id()

    if current_device is None:
        return False

    conn = sqlite3.connect(DEVICES_DB)
    cur = conn.cursor()

    cur.execute("""
        SELECT device_id
        FROM devices
        WHERE owner = ?
    """, (username,))

    rows = cur.fetchall()

    conn.close()

    for (device_id,) in rows:
        if str(device_id) == current_device:
            return True

    return False


# ==================================================
# ROLE ACCESS
# ==================================================

def can_access_file(file_id, user_role):

    conn = sqlite3.connect(FILES_DB)

    cur = conn.cursor()

    cur.execute("""
        SELECT allowed_roles
        FROM files
        WHERE file_id=?
    """, (file_id,))

    row = cur.fetchone()

    conn.close()

    if not row:

        return False

    try:

        allowed_roles = json.loads(row[0])

    except Exception:

        return False

    return user_role in allowed_roles


# ==================================================
# GET FILE ID
# ==================================================

def get_file_id(filename):

    conn = sqlite3.connect(FILES_DB)

    cur = conn.cursor()

    cur.execute("""
        SELECT file_id
        FROM files
        WHERE filename=?
    """, (filename,))

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return None

# ==================================================
# MAIN DECRYPTION
# ==================================================


def decrypt_file_core(username, file_path):
    """
    Pure worker logic: DB lookups, device/role checks, AES decryption,
    file I/O. No QFileDialog / QMessageBox calls in here — safe to run
    on a background QThread so a large file doesn't freeze the GUI.

    Returns (success: bool, message: str, output_path: str or None)
    """

    file_id = "UNKNOWN"

    try:

        filename = os.path.basename(file_path)

        file_id = get_file_id(filename)

        if file_id is None:
            log_event(username, "UNKNOWN", "DECRYPT_FAILED", "Unknown File")
            return False, "File is not registered in the database.", None

        user_role = get_user_role(username)

        if user_role is None:
            log_event(username, file_id, "DECRYPT_FAILED", "Unknown User")
            return False, "User not found.", None

        if not verify_device(username):
            log_event(username, file_id, "DEVICE_DENIED", "Unregistered Device")
            return False, "This device is not registered.", None

        if not can_access_file(file_id, user_role):
            log_event(username, file_id, "ROLE_DENIED", user_role)
            return False, f"{user_role} does not have permission to access this file.", None

        key = get_aes_key(file_id)

        if key is None:
            log_event(username, file_id, "DECRYPT_FAILED", "AES Key Missing")
            return False, "Encryption key not found.", None

        with open(file_path, "rb") as f:
            extension = f.read(16)
            nonce = f.read(16)
            tag = f.read(16)
            ciphertext = f.read()

        extension = extension.decode("utf-8").rstrip("\x00")

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)

        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

        output_path = os.path.splitext(file_path)[0] + extension

        with open(output_path, "wb") as f:
            f.write(decrypted_data)

        log_event(username, file_id, "DECRYPT_SUCCESS", f"Role={user_role}")

        return True, f"File decrypted successfully.\n\n{output_path}", output_path

    except Exception as e:

        log_event(
            username,
            file_id,
            "DECRYPT_FAILED",
            str(e)
        )

        return False, str(e), None


def decrypt_file(username, file_path=None):
    """
    Synchronous, dialog-driven convenience wrapper around decrypt_file_core.
    Only safe to call from the GUI (main) thread. GUI callers that want to
    stay responsive on large files should instead: pick the file with
    QFileDialog on the main thread, run decrypt_file_core() on a QThread,
    and show the result dialog from a slot connected to that thread's
    finished signal.
    """

    if not file_path:

        app = QApplication.instance() or QApplication(sys.argv)

        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Encrypted File",
            "",
            "DAPS Files (*.daps)"
        )

        if not file_path:
            return None

    success, message, output_path = decrypt_file_core(username, file_path)

    if success:
        QMessageBox.information(None, "Success", message)
    else:
        QMessageBox.warning(None, "Decryption Failed", message)

    return output_path


if __name__ == "__main__":

    path = sys.argv[1] if len(sys.argv) > 1 else None

    result = decrypt_file("admin", path)

    if result:

        print(result)