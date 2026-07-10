import ctypes
from ctypes import wintypes

cfgmgr32 = ctypes.windll.cfgmgr32

CR_SUCCESS = 0x00000000
CM_DRP_CAPABILITIES = 0x00000010
CM_DRP_DEVICEDESC = 0x00000001
CM_DRP_FRIENDLYNAME = 0x0000000D

# Known capability bit meanings (from cfgmgr32.h) for reference when reading output
CAPABILITY_FLAGS = {
    0x00000001: "LOCKSUPPORTED",
    0x00000002: "EJECTSUPPORTED",
    0x00000004: "REMOVABLE",
    0x00000008: "DOCKDEVICE",
    0x00000010: "UNIQUEID",
    0x00000020: "SILENTINSTALL",
    0x00000040: "RAWDEVICEOK",
    0x00000080: "SURPRISEREMOVALOK",
    0x00000100: "HARDWAREDISABLED",
    0x00000200: "NONDYNAMIC",
}


def get_devinst_from_pnp_id(pnp_device_id: str):
    devinst = wintypes.ULONG()
    result = cfgmgr32.CM_Locate_DevNodeW(
        ctypes.byref(devinst), pnp_device_id, 0
    )
    if result != CR_SUCCESS:
        print(f"CM_Locate_DevNodeW failed, CR={result}")
        return None
    return devinst.value


def get_device_id(devinst: int) -> str:
    buf = ctypes.create_unicode_buffer(512)
    cfgmgr32.CM_Get_Device_IDW(devinst, buf, 512, 0)
    return buf.value


def get_string_property(devinst: int, prop: int) -> str:
    buf = ctypes.create_unicode_buffer(512)
    size = wintypes.ULONG(ctypes.sizeof(buf))
    result = cfgmgr32.CM_Get_DevNode_Registry_PropertyW(
        devinst, prop, None, buf, ctypes.byref(size), 0
    )
    if result != CR_SUCCESS:
        return f"<unavailable, CR={result}>"
    return buf.value


def get_capabilities(devinst: int):
    caps = wintypes.ULONG(0)
    size = wintypes.ULONG(ctypes.sizeof(caps))
    result = cfgmgr32.CM_Get_DevNode_Registry_PropertyW(
        devinst, CM_DRP_CAPABILITIES, None, ctypes.byref(caps), ctypes.byref(size), 0
    )
    if result != CR_SUCCESS:
        return None, result
    return caps.value, result


def decode_flags(value: int):
    if value is None:
        return "(none / property missing)"
    matched = [name for bit, name in CAPABILITY_FLAGS.items() if value & bit]
    return f"0x{value:08X} -> {', '.join(matched) if matched else '(no known flags set)'}"


def walk_chain(pnp_device_id: str, max_depth: int = 12):
    devinst = get_devinst_from_pnp_id(pnp_device_id)
    if devinst is None:
        print("Could not resolve starting devinst. Check the pnp_device_id string.")
        return

    current = devinst
    for depth in range(max_depth):
        dev_id = get_device_id(current)
        desc = get_string_property(current, CM_DRP_FRIENDLYNAME)
        if desc.startswith("<unavailable"):
            desc = get_string_property(current, CM_DRP_DEVICEDESC)
        caps_val, caps_cr = get_capabilities(current)

        print(f"--- depth {depth} | devinst {current} ---")
        print(f"  Device ID     : {dev_id}")
        print(f"  Description   : {desc}")
        print(f"  Capabilities  : {decode_flags(caps_val)}")
        if caps_cr != CR_SUCCESS:
            print(f"  (CM_Get_DevNode_Registry_PropertyW returned CR={caps_cr} for capabilities)")
        print()

        parent = wintypes.ULONG()
        result = cfgmgr32.CM_Get_Parent(ctypes.byref(parent), current, 0)
        if result != CR_SUCCESS:
            print(f"Reached top of tree (CM_Get_Parent CR={result}). Stopping.\n")
            break
        current = parent.value


if __name__ == "__main__":
    # Paste the exact pnp_device_id string printed by usb_info.py for your SSD
    test_pnp_id = r"SCSI\DISK&VEN_EVM_EXTE&PROD_RNAL_SSD_256\6&530062A&1&000000"
    walk_chain(test_pnp_id)