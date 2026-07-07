import time
import sqlite3
from pathlib import Path
from datetime import datetime

import wmi

from usb_auth import USBAuthenticator
from usb_eject import USBEjector


# ==========================================================
# DATABASE
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

LOGS_DB = ROOT_DIR / "database" / "logs.db"


# ==========================================================
# AUDIT LOG
# ==========================================================

def log_event(action, details=""):

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
        "SYSTEM",
        "-",
        "-",
        action,
        details
    ))

    conn.commit()

    conn.close()


# ==========================================================
# USB MONITOR
# ==========================================================

class USBMonitor:

    def __init__(self):

        self.wmi = wmi.WMI()

        self.auth = USBAuthenticator()

        self.ejector = USBEjector()

    # ------------------------------------------------------

    def start(self):

        print("\nUSB Monitor Started...\n")

        watcher = self.wmi.watch_for(

            notification_type="Creation",

            wmi_class="Win32_USBControllerDevice"

        )

        while True:

            try:

                watcher()

                print("\nUSB Device Inserted\n")

                results = self.auth.authenticate_all()

                if not results:

                    continue

                for item in results:

                    usb = item["device"]

                    serial = usb["serial_number"]

                    log_event(

                        "USB_INSERTED",

                        serial

                    )

                    if item["authorized"]:

                        print(

                            "[AUTHORIZED]",

                            usb["device_name"]

                        )

                        log_event(

                            "USB_AUTHORIZED",

                            serial

                        )

                    else:

                        print(

                            "[UNAUTHORIZED]",

                            usb["device_name"]

                        )

                        log_event(

                            "USB_BLOCKED",

                            serial

                        )

                        self.ejector.eject(

                            usb

                        )

            except KeyboardInterrupt:

                print(

                    "\nUSB Monitor Stopped."

                )

                break

            except Exception as e:

                print(

                    "USB Monitor Error:",

                    e

                )

                time.sleep(1)


# ==========================================================
# TEST
# ==========================================================

if __name__ == "__main__":

    monitor = USBMonitor()

    monitor.start()