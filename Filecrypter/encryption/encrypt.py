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
from GUI_modules.progess_dialog import ProgressDialog

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

def move_to_company_database(file_path):

    os.makedirs(COMPANY_DB, exist_ok=True)

    destination = os.path.join(
        COMPANY_DB,
        os.path.basename(file_path)
    )

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

        # ---------------------------------------
        # Get User Details
        # ---------------------------------------

        department, user_role = get_user_details(username)

        if department is None:

            QMessageBox.warning(
                None,
                "Error",
                "User not found."
            )

            return None

        # ---------------------------------------
        # Encryption Settings Dialog
        # ---------------------------------------

        dialog = RoleSelectionDialog(user_role)

        if not dialog.exec():

            return None

        classification, allowed_roles = dialog.get_data()

        # ---------------------------------------
        # Generate File ID
        # ---------------------------------------

        file_id = str(uuid.uuid4())

        # ---------------------------------------
        # Generate AES Key
        # ---------------------------------------

        key = generate_aes_key()

        save_key(file_id, key)

        # ---------------------------------------
        # Read Original File
        # ---------------------------------------

        filename = os.path.basename(file_path)

        _, extension = os.path.splitext(filename)

        extension = extension.encode("utf-8").ljust(16, b"\x00")

        with open(file_path, "rb") as f:

            original_data = f.read()

        # ---------------------------------------
        # AES-256 Encryption
        # ---------------------------------------

        cipher = AES.new(
            key,
            AES.MODE_GCM
        )

        ciphertext, tag = cipher.encrypt_and_digest(
            original_data
        )

        encrypted_file = (
            os.path.splitext(file_path)[0]
            + ".tvk"
        )

        with open(encrypted_file, "wb") as f:

            f.write(extension)
            f.write(cipher.nonce)
            f.write(tag)
            f.write(ciphertext)

        # ---------------------------------------
        # Move to Company Database
        # ---------------------------------------

        encrypted_file = move_to_company_database(
            encrypted_file
        )

        # ---------------------------------------
        # Save Metadata
        # ---------------------------------------

        save_file_metadata(

            file_id=file_id,

            filename=os.path.basename(
                encrypted_file
            ),

            path=encrypted_file,

            classification=classification,

            department=department,

            allowed_roles=allowed_roles

        )

        # ---------------------------------------
        # Audit Log
        # ---------------------------------------

        log_event(

            username=username,

            file_id=file_id,

            action="ENCRYPT_SUCCESS",

            details=f"Classification={classification}"

        )

        QMessageBox.information(

            None,

            "Encryption Successful",

            f"Encrypted file stored in:\n\n{encrypted_file}"

        )

        return encrypted_file

    except Exception as e:

        print("Encryption Error:", e)

        log_event(

            username=username,

            file_id=file_id if "file_id" in locals() else "UNKNOWN",

            action="ENCRYPT_FAILED",

            details=str(e)

        )

        QMessageBox.critical(

            None,

            "Encryption Failed",

            str(e)

        )

        return None