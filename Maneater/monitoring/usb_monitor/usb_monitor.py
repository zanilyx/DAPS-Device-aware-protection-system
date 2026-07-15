import logging
import time
import sys
from pathlib import Path

alerts_dir = Path(__file__).resolve().parent.parent.parent 
if str(alerts_dir) not in sys.path:
    sys.path.insert(0, str(alerts_dir))

from alerts.alert_manager import raise_alert, Severity
usb_dir= alerts_dir / "monitoring" / "usb_monitor"
if str(usb_dir) not in sys.path:
    sys.path.insert(0, str(usb_dir))
from usb_auth import USBAuthenticator
from usb_eject import eject_physical_drive, disable_by_pnp_id
from usb_log import log_event

# ===================================================
# Config
# ===================================================

POLL_INTERVAL_SECONDS = 3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


# ===================================================
# Enforcement for a single unauthorized device
# ===================================================

def enforce_device(usb: dict, device_hash: str):

    name = usb["device_name"]
    pnp_id = usb["pnp_device_id"]
    usb_type = usb.get("media_type") or name

    logging.warning(f"Unauthorized device detected: {name} ({pnp_id})")

    log_event(device_hash, usb_type, "DEVICE_DETECTED", "UNAUTHORIZED")

    raise_alert(
        source="USB",
        severity=Severity.WARNING,
        title="Unknown USB device connected",
        message=f"{name} ({pnp_id}) is not authorized."
    )


    # Try safe eject only for storage devices
    if usb.get("physical_drive"):

        ok = eject_physical_drive(usb["physical_drive"])

        logging.info(
            f"IOCTL eject {'succeeded' if ok else 'failed/vetoed'} for {name}"
        )

        log_event(
            device_hash,
            usb_type,
            "EJECT_ATTEMPT",
            "SUCCESS" if ok else "FAILED"
        )

    else:

        logging.info(
            f"{name} is an MTP/Portable device. Skipping eject."
        )

    # Attempt to disable device
    disabled = disable_by_pnp_id(pnp_id)

    if disabled:

        logging.warning(f"Device disabled: {name}")

        log_event(
            device_hash,
            usb_type,
            "DEVICE_DISABLED",
            "SUCCESS"
        )

        raise_alert(
            source="USB",
            severity=Severity.INFO,
            title="Unauthorized USB blocked",
            message=f"{name} was successfully disabled."
        )

    else:

        logging.error(f"Device disable FAILED for {name}")

        log_event(
            device_hash,
            usb_type,
            "DEVICE_DISABLED",
            "FAILED"
        )

        raise_alert(
            source="USB",
            severity=Severity.CRITICAL,
            title="Failed to block unauthorized USB device",
            message=f"{name} could not be disabled. Workstation will remain locked until the device is removed."
        )

        logging.warning("Waiting for unauthorized device removal...")

        wait_until_removed(pnp_id)

        logging.info("Unauthorized device removed.")


# ===================================================
# Main monitor loop
# ===================================================

def monitor(stop_event=None):
    auth = USBAuthenticator()
    known_ids = set()

    logging.info("USB monitor started. Watching for new devices...")

    while stop_event is None or not stop_event.is_set():
        try:
            results = auth.authenticate_all()
            current_ids = set()

            for item in results:
                usb = item["device"]
                dev_key = usb["pnp_device_id"]
                current_ids.add(dev_key)

                if dev_key in known_ids:
                    continue  # already processed this device, skip

                device_hash = auth.generate_device_hash(usb)
                usb_type = usb.get("media_type") or usb["device_name"]

                # newly seen device this cycle
                if item["authorized"]:
                    logging.info(f"Authorized device connected: {usb['device_name']} (owner: {item['owner']})")
                    log_event(device_hash, usb_type, "DEVICE_DETECTED", "AUTHORIZED")
                else:
                    enforce_device(usb, device_hash)

            # forget devices that were unplugged, so they're re-checked if reconnected
            known_ids = current_ids

        except Exception as e:
            logging.error(f"Monitor loop error: {e}")
            log_event("", "", "MONITOR_ERROR", "FAILED")
            raise_alert(
                source="USB",
                severity=Severity.CRITICAL,
                title="USB monitor error",
                message=str(e)
            )

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        monitor()
    except KeyboardInterrupt:
        logging.info("USB monitor stopped by user.")