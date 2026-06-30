import os
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QFileDialog
from Crypto.Cipher import AES
import sqlite3
import base64
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

USERS_DB   = ROOT_DIR / "database" / "users.db"
DEVICES_DB = ROOT_DIR / "database" / "devices.db"
FILES_DB   = ROOT_DIR / "database" / "files.db"
LOGS_DB    = ROOT_DIR / "database" / "logs.db"
def get_aes_key(file_id):

    conn = sqlite3.connect(FILES_DB)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT aes_key
        FROM files
        WHERE file_id=?
        """,
        (file_id,)
    )

    row = cur.fetchone()

    conn.close()

    if row is None:
        return None

    return base64.b64decode(row[0])

def encrypt_file(file_path=None):
    if not file_path:
        app = QApplication.instance() or QApplication(sys.argv)
        file_path, _ = QFileDialog.getOpenFileName(None, "Select File to Encrypt", "")
        if not file_path:
            return None

    try:
        key = get_aes_key()
        
        # Extract and encode the original extension (e.g., '.txt' -> max 16 bytes for padding)
        _, ext = os.path.splitext(file_path)
        ext_encoded = ext.encode('utf-8').ljust(16, b'\x00') # Pad to fixed 16 bytes

        with open(file_path, "rb") as f:
            data = f.read()

        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)

        # New extension setup
        output_path = os.path.splitext(file_path)[0] + ".tvk"
        
        # Save: Ext (16B) + Nonce (16B) + Tag (16B) + Ciphertext
        with open(output_path, "wb") as f:
            for item in (ext_encoded, cipher.nonce, tag, ciphertext):
                f.write(item)

        return output_path
    except Exception as e:
        print(f"Encryption error: {e}")
        return None

if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = encrypt_file(path_arg)
    if result:
        print(f"Successfully encrypted to: {result}")