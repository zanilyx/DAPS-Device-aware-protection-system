import os
import sys
import uuid
import json
import shutil
import sqlite3
import base64

import time
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox
)

from Crypto.Cipher import AES

from .key import build_metadata, generate_key
from .decrypt import log_event
from GUI_modules.role_dialog import RoleSelectionDialog

# ==========================================================
# DATABASE PATHS
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

USERS_DB = ROOT_DIR / "database" / "users.db"
FILES_DB = ROOT_DIR / "database" / "files.db"
KEYS_DB = ROOT_DIR / "database" / "keys.db"

# Simulated Company Server
COMPANY_DB = r"C:\Piyush\Projects\CCNCS\Files\code\Company DB"


# ==========================================================
# AES KEY GENERATION
# ==========================================================

def generate_aes_key():

    metadata = build_metadata()

    return generate_key(metadata)


# ==========================================================
# STORE AES KEY
# ==========================================================

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


# ==========================================================
# USER DETAILS
# ==========================================================

def get_user_details(username):

    conn = sqlite3.connect(USERS_DB)

    cur = conn.cursor()

    cur.execute("""
        SELECT department,
               role
        FROM users
        WHERE username=?
    """,
    (username,)
    )

    row = cur.fetchone()

    conn.close()

    if row:

        return row[0], row[1]

    return None, None


# ==========================================================
# MOVE FILE TO COMPANY DATABASE
# ==========================================================

def get_company_db_destination(file_path):
    """Computes where a file will end up in Company DB, creating the
    folder if needed, without actually moving anything yet."""

    os.makedirs(COMPANY_DB, exist_ok=True)

    return os.path.join(
        COMPANY_DB,
        os.path.basename(file_path)
    )


def move_to_company_database(file_path, destination=None):

    if destination is None:
        destination = get_company_db_destination(file_path)

    # If the file is already sitting at the destination (e.g. the user
    # picked an already-encrypted .daps file that lives in Company DB),
    # source and destination are the same path. Removing "destination"
    # in that case deletes the very file we're about to move, so just
    # treat it as already in place instead of moving it onto itself.
    if os.path.abspath(file_path) == os.path.abspath(destination):
        return destination

    if os.path.exists(destination):
        os.remove(destination)

    shutil.move(file_path, destination)

    return destination


# ==========================================================
# SAVE FILE METADATA
# ==========================================================

def save_file_metadata(
        file_id,
        filename,
        path,
        classification,
        department,
        allowed_roles):

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
            allowed_roles,
            access_type
        )

        VALUES
        (?, ?, ?, ?, ?, ?, ?)
    """,
    (
        file_id,
        filename,
        path,
        classification,
        department,
        json.dumps(allowed_roles),
        "Read/Write"
    ))

    conn.commit()
    conn.close()


def encrypt_file_core(username, file_path, classification, allowed_roles):
    """
    Pure worker logic: key generation, AES encryption, file I/O, DB writes.
    No QFileDialog / RoleSelectionDialog / QMessageBox calls in here —
    this is what makes it safe to run on a background QThread instead of
    the GUI thread, so a large file doesn't freeze the interface.

    Returns (success: bool, message: str, output_path: str or None)
    """

    file_id = "UNKNOWN"

    try:

        department, user_role = get_user_details(username)

        if department is None:
            return False, "User not found.", None

        file_id = str(uuid.uuid4())

        key = generate_aes_key()

        save_key(file_id, key)

        filename = os.path.basename(file_path)

        _, extension = os.path.splitext(filename)

        extension = extension.encode("utf-8").ljust(16, b"\x00")

        with open(file_path, "rb") as f:
            original_data = f.read()

        cipher = AES.new(key, AES.MODE_GCM)

        ciphertext, tag = cipher.encrypt_and_digest(original_data)

        encrypted_file = os.path.splitext(file_path)[0] + ".daps"

        with open(encrypted_file, "wb") as f:
            f.write(extension)
            f.write(cipher.nonce)
            f.write(tag)
            f.write(ciphertext)

        # Register in files.db BEFORE the physical move (see file_watchdog notes).
        destination_path = get_company_db_destination(encrypted_file)

        save_file_metadata(
            file_id=file_id,
            filename=os.path.basename(destination_path),
            path=destination_path,
            classification=classification,
            department=department,
            allowed_roles=allowed_roles
        )

        encrypted_file = move_to_company_database(
            encrypted_file,
            destination=destination_path
        )

        log_event(
            username=username,
            file_id=file_id,
            action="ENCRYPT_SUCCESS",
            details=f"Classification={classification}"
        )

        # Remove original plaintext file from device — confidential files
        # should only exist as the encrypted .daps in Company DB.
        original_removed = True
        same_path = os.path.abspath(file_path) == os.path.abspath(encrypted_file)

        try:
            if not same_path and os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            original_removed = False
            log_event(
                username=username,
                file_id=file_id,
                action="ORIGINAL_DELETE_FAILED",
                details=str(e)
            )

        if original_removed:
            message = (
                f"Encrypted file stored in:\n\n{encrypted_file}\n\n"
            )
        else:
            message = (
                f"Encrypted file stored in:\n\n{encrypted_file}\n\n"
                f"Could not remove the original file from this device. "
            )

        return True, message, encrypted_file

    except Exception as e:

        print("Encryption Error:", e)

        log_event(
            username=username,
            file_id=file_id,
            action="ENCRYPT_FAILED",
            details=str(e)
        )

        return False, str(e), None


def encrypt_file(username, file_path=None):
    """
    Synchronous, dialog-driven convenience wrapper around encrypt_file_core.
    Only safe to call from the GUI (main) thread, since it opens
    QFileDialog / RoleSelectionDialog / QMessageBox. GUI callers that want
    to stay responsive on large files should instead: pick the file with
    QFileDialog on the main thread, run encrypt_file_core() on a QThread,
    and show the result dialog from a slot connected to that thread's
    finished signal.
    """

    if not file_path:

        app = QApplication.instance() or QApplication(sys.argv)

        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select File to Encrypt",
            ""
        )

        if not file_path:
            return None

    department, user_role = get_user_details(username)

    if department is None:
        QMessageBox.warning(None, "Error", "User not found.")
        return None

    dialog = RoleSelectionDialog(user_role)

    if not dialog.exec():
        return None

    classification, allowed_roles = dialog.get_data()

    success, message, output_path = encrypt_file_core(
        username, file_path, classification, allowed_roles
    )

    if success:
        QMessageBox.information(None, "Encryption Successful", message)
    else:
        QMessageBox.critical(None, "Encryption Failed", message)

    return output_path