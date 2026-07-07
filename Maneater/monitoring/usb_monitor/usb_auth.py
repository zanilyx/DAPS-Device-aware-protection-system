import hashlib
import sqlite3
from pathlib import Path

from usb_info import USBInfo


ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

USB_DB = ROOT_DIR / "database" / "devices.db"


class USBAuthenticator:

    def __init__(self):

        self.usb = USBInfo()

    # ===================================================
    # Generate Device Hash
    # ===================================================

    def generate_device_hash(self, device):

        device_string = (
            f"{device['manufacturer']}|"
            f"{device['model']}|"
            f"{device['pnp_device_id']}"
        )

        return hashlib.sha256(
            device_string.encode()
        ).hexdigest()

    # ===================================================
    # Authenticate One USB
    # ===================================================

    def authenticate_device(self, device):

        device_hash = self.generate_device_hash(device)

        conn = sqlite3.connect(USB_DB)

        cur = conn.cursor()

        cur.execute("""

            SELECT owner

            FROM usb_devices

            WHERE device_id=?

        """,

        (device_hash,))

        row = cur.fetchone()

        conn.close()

        if row:

            return True, row[0]

        return False, None

    # ===================================================
    # Authenticate All Connected USBs
    # ===================================================

    def authenticate_all(self):

        devices = self.usb.get_connected_usb_devices()

        results = []

        for device in devices:

            status, owner = self.authenticate_device(device)

            results.append({

                "device": device,

                "authorized": status,

                "owner": owner

            })

        return results


# ===================================================
# TEST
# ===================================================

if __name__ == "__main__":

    auth = USBAuthenticator()

    devices = auth.authenticate_all()

    if not devices:

        print("\nNo USB Storage Device Connected.\n")

    else:

        for item in devices:

            usb = item["device"]

            print("-----------------------------------")

            print("Device Name :", usb["device_name"])

            print("Manufacturer  :", usb["manufacturer"])
            print("Model         :", usb["model"])
            print("PNP Device ID  :", usb["pnp_device_id"])

            print()

            if item["authorized"]:

                print("STATUS : AUTHORIZED")

                print("OWNER  :", item["owner"])

            else:

                print("STATUS : UNAUTHORIZED")

            print("-----------------------------------\n")