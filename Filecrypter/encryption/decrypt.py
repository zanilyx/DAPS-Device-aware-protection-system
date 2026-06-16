import os
import sys
from PySide6.QtWidgets import QApplication, QFileDialog
from Crypto.Cipher import AES

def get_aes_key():
    secret_input = "my_super_secret_key_password_123"
    return secret_input.ljust(32, '0')[:32].encode('utf-8')

def decrypt_file(file_path=None):
    if not file_path:
        app = QApplication.instance() or QApplication(sys.argv)
        file_path, _ = QFileDialog.getOpenFileName(None, "Select File to Decrypt", "", "TVK Files (*.tvk)")
        if not file_path:
            return None

    try:
        key = get_aes_key()

        # Read layout components
        with open(file_path, "rb") as f:
            ext_encoded = f.read(16)
            nonce = f.read(16)
            tag = f.read(16)
            ciphertext = f.read()

        # Decode extension and strip padding zeroes
        orig_ext = ext_encoded.decode('utf-8').rstrip('\x00')

        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)

        # Build output path using the recovered original extension
        output_path = os.path.splitext(file_path)[0] + orig_ext
        
        with open(output_path, "wb") as f:
            f.write(decrypted_data)

        return output_path
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = decrypt_file(path_arg)
    if result:
        print(f"Successfully decrypted back to: {result}")