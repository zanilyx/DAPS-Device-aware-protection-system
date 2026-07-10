import ctypes
from ctypes import wintypes

from usb_auth import USBAuthenticator


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
cfgmgr32 = ctypes.WinDLL("cfgmgr32", use_last_error=True)

CR_SUCCESS = 0x00000000
CM_DISABLE_UI_NOT_OK = 0x00000001  # fail rather than prompt UI if disable needs confirmation

GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# IOCTL codes (computed from CTL_CODE(FILE_DEVICE_MASS_STORAGE, ..., METHOD_BUFFERED, FILE_READ_ACCESS))
IOCTL_STORAGE_EJECT_MEDIA = 0x2D4808
IOCTL_STORAGE_MEDIA_REMOVAL = 0x2D4804


def _open_device(path: str):
    handle = kernel32.CreateFileW(
        path,
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None
    )
    if handle in (None, 0, INVALID_HANDLE_VALUE):
        return None
    return handle


def _device_io_control(handle, code: int) -> bool:
    bytes_returned = wintypes.DWORD(0)
    ok = kernel32.DeviceIoControl(
        handle,
        code,
        None, 0,
        None, 0,
        ctypes.byref(bytes_returned),
        None
    )
    return bool(ok)


# ===================================================
# Eject via raw physical drive handle
# (works even when the devnode chain has no
# CM_DEVCAP_EJECTSUPPORTED node, e.g. UASP SSD bridges)
# ===================================================

def eject_physical_drive(physical_drive_path: str) -> bool:
    """
    physical_drive_path example: r"\\.\PHYSICALDRIVE1"
    This matches device['physical_drive'] from usb_info.py (disk.DeviceID).
    """
    handle = _open_device(physical_drive_path)
    if handle is None:
        err = ctypes.get_last_error()
        print(f"Failed to open {physical_drive_path}. Win32 error={err}")
        return False

    try:
        # Tell the driver removal is allowed (PREVENT_MEDIA_REMOVAL = FALSE).
        # Some drivers require this before honoring an eject request.
        _device_io_control(handle, IOCTL_STORAGE_MEDIA_REMOVAL)

        ok = _device_io_control(handle, IOCTL_STORAGE_EJECT_MEDIA)
        if not ok:
            err = ctypes.get_last_error()
            print(f"IOCTL_STORAGE_EJECT_MEDIA failed. Win32 error={err}")
            print("  (commonly ERROR_ACCESS_DENIED=5 if a file/handle is open on the drive)")
        return ok
    finally:
        kernel32.CloseHandle(handle)


# ===================================================
# Disable the device node (fallback for hardware that
# doesn't implement software eject at all, e.g. this
# SSD's UASP bridge which has no EJECTSUPPORTED flag
# anywhere in its devnode chain)
# ===================================================

def get_devinst_from_pnp_id(pnp_device_id: str):
    devinst = wintypes.ULONG()
    result = cfgmgr32.CM_Locate_DevNodeW(ctypes.byref(devinst), pnp_device_id, 0)
    if result != CR_SUCCESS:
        return None
    return devinst.value


def disable_devnode(devinst: int) -> bool:
    result = cfgmgr32.CM_Disable_DevNode(devinst, CM_DISABLE_UI_NOT_OK)
    return result == CR_SUCCESS


def disable_by_pnp_id(pnp_device_id: str) -> bool:
    """
    Resolves the disk's devnode, walks up one level to the actual
    USB function device (e.g. USB\\VID_xxxx&PID_xxxx\\...), and
    disables it. This is equivalent to Device Manager > Disable
    device, and unlike CM_Request_Device_Eject it does not require
    the driver to advertise CM_DEVCAP_EJECTSUPPORTED.
    """
    disk_devinst = get_devinst_from_pnp_id(pnp_device_id)
    if disk_devinst is None:
        print(f"Could not locate DevInst for {pnp_device_id}")
        return False

    parent = wintypes.ULONG()
    result = cfgmgr32.CM_Get_Parent(ctypes.byref(parent), disk_devinst, 0)
    target_devinst = parent.value if result == CR_SUCCESS else disk_devinst

    ok = disable_devnode(target_devinst)
    if not ok:
        print(f"CM_Disable_DevNode failed for devinst {target_devinst}")
    return ok


# ===================================================
# Full workflow: authenticate, then eject unauthorized
# ===================================================

def enforce():
    auth = USBAuthenticator()
    results = auth.authenticate_all()

    for item in results:
        usb = item["device"]

        if item["authorized"]:
            print(f"[OK] {usb['device_name']} ({item['owner']}) authorized.")
            continue

        print(f"[MISMATCH] {usb['device_name']} ({usb['pnp_device_id']}) unauthorized. Ejecting...")

        ok = eject_physical_drive(usb["physical_drive"])
        if ok:
            print("  IOCTL eject reported success.")
        else:
            print("  IOCTL eject failed/vetoed.")

        # Many bridge chips (like this one) ack the IOCTL without doing
        # anything physically. Disable the devnode as a hard fallback
        # so the device is actually unusable regardless of driver support.
        print("  Disabling device node as enforcement fallback...")
        disabled = disable_by_pnp_id(usb["pnp_device_id"])
        print("  Device disabled." if disabled else "  Device disable failed/vetoed.")


if __name__ == "__main__":
    enforce()