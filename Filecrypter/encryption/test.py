import winreg
import socket


# ==========================================================
# This mirrors get_device_id() / get_hostname() in decrypt.py
# EXACTLY, so the value printed here is guaranteed to match
# what verify_device() will check against later.
#
# Run this ON the laptop you want to register (not on the
# machine that manages the database), then copy the printed
# device_id into your devices.db entry for that user/laptop.
# ==========================================================

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

    except Exception as e:
        print("Could not read MachineGuid:", e)
        return None


def get_hostname():
    return socket.gethostname()


if __name__ == "__main__":

    device_id = get_device_id()
    hostname = get_hostname()

    print("=" * 60)
    print(f"Hostname   : {hostname}")
    print(f"Device ID  : {device_id}")
    print("=" * 60)

    if device_id:
        print("\nReady-to-use SQL insert (edit owner/table columns as needed):\n")
        print(
            f'INSERT INTO devices (owner, device_id) VALUES '
            f'("<username>", "{device_id}");'
        )
    else:
        print("\nCould not generate a device ID on this machine.")