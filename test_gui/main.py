import psutil, socket
for name, addrs in psutil.net_if_addrs().items():
    for addr in addrs:
        if addr.family == socket.AF_INET6:
            print(f"{name}: {addr.address!r}")