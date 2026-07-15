import re

from numpy import info
import wmi


class USBInfo:

    def __init__(self):

        self.wmi = wmi.WMI()

    # -----------------------------------------------------

    def get_connected_usb_devices(self):

        devices = []

        for disk in self.wmi.Win32_DiskDrive():

    # Ignore internal drives
            if disk.MediaType:

                if "Fixed" in disk.MediaType:
                    continue

            info = {}

            info["device_name"] = disk.Caption

            info["manufacturer"] = disk.Manufacturer

            info["model"] = disk.Model

            info["physical_drive"] = disk.DeviceID

            info["pnp_device_id"] = disk.PNPDeviceID

            info["media_type"] = disk.MediaType


            devices.append(info)

        return devices


# ---------------------------------------------------------
# MTP / Portable devices (Android, iPhone, etc.) are not listed in Win32_DiskDrive.
# ---------------------------------------------------------

    def get_connected_mtp_devices(self):

        devices = []

        for dev in self.wmi.Win32_PnPEntity():

            if not dev.PNPDeviceID:
                continue

            if not dev.PNPDeviceID.startswith("USB\\"):
                continue

            # Skip USB hubs
            if "ROOT_HUB" in dev.PNPDeviceID:
                continue

            # Skip USB composite devices
            if dev.Name and "Composite" in dev.Name:
                continue

            # Skip webcams
            if dev.Name and "WebCam" in dev.Name:
                continue

            info = {}

            info["device_name"] = dev.Name
            info["manufacturer"] = dev.Manufacturer
            info["model"] = dev.Name
            info["physical_drive"] = None
            info["pnp_device_id"] = dev.PNPDeviceID
            info["media_type"] = "USB"

            devices.append(info)

        return devices
# ---------------------------------------------------------
# All connected USB devices (storage + MTP/portable)
# ---------------------------------------------------------

    def get_all_usb_devices(self):

        devices = []

        devices.extend(self.get_connected_usb_devices())   # Storage devices
   # Phones

        return devices
# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":
    import hashlib
    usb = USBInfo()

    devices = usb.get_connected_usb_devices()

    if not devices:

        print("\nNo USB storage device connected.\n")

    else:

        print(f"\n{len(devices)} USB device(s) detected.\n")

        for i, device in enumerate(devices, start=1):

            print(f"---------- USB Device {i} ----------")

            print("Device Name :", device["device_name"])

            print("Manufacturer  :", device["manufacturer"])
            print("Model         :", device["model"])


            print("PNP Device ID  :", device["pnp_device_id"])

            device_string = (
                f"{device['manufacturer']}|"
                f"{device['model']}|"
                f"{device['pnp_device_id']}"
            )

            device_hash = hashlib.sha256(
                device_string.encode()
            ).hexdigest()
            print("hashed value: ",device_hash)
            print()