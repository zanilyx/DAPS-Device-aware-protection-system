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

            is_external = False

            if disk.MediaType:

                if "External" in disk.MediaType:
                    is_external = True

            if disk.InterfaceType == "USB":
                is_external = True

            if disk.PNPDeviceID.startswith("USB"):
                is_external = True

            if not is_external:
                continue

            info = {}

            info["device_name"] = disk.Caption

            info["manufacturer"] = disk.Manufacturer

            info["physical_drive"] = disk.DeviceID

            info["pnp_device_id"] = disk.PNPDeviceID

            info["serial_number"] = self.get_serial_number(
                disk.PNPDeviceID
            )

            vid, pid = self.get_vid_pid(
                disk.PNPDeviceID
            )

            info["vid"] = vid

            info["pid"] = pid

            devices.append(info)

        return devices

    # -----------------------------------------------------

    def get_vid_pid(self, pnp_id):

        vid = ""
        pid = ""

        vid_match = re.search(r"VID_([0-9A-F]{4})", pnp_id, re.I)

        pid_match = re.search(r"PID_([0-9A-F]{4})", pnp_id, re.I)

        if vid_match:
            vid = vid_match.group(1)

        if pid_match:
            pid = pid_match.group(1)

        return vid, pid

    # -----------------------------------------------------

    def get_serial_number(self, pnp_id):

        try:

            serial = pnp_id.split("\\")[-1]

            if "&" in serial:

                serial = serial.split("&")[0]

            return serial

        except Exception:

            return ""



# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":

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

            print("VID           :", device["vid"])

            print("PID           :", device["pid"])

            print("Serial Number :", device["serial_number"])

            print("Physical Drive :", device["physical_drive"])

            print("PNP Device ID  :", device["pnp_device_id"])

            print()