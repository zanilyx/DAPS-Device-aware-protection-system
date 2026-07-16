# import uuid
# from pathlib import Path
# print(str(uuid.getnode()))
# import sqlite3

# current_device = str(uuid.getnode())

import winreg


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

        return machine_guid

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("DAPS Device Registration")
    print("=" * 50)

    device_id = get_device_id()

    if device_id:
        print(f"\nDevice ID : {device_id}")
    else:
        print("\nFailed to retrieve Device ID.")

    print("=" * 50)