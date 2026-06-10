import tkinter as tk
from tkinter import ttk
import psutil
import socket
import threading
import time

class NetworkMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Outbound Connection Monitor")
        self.root.geometry("900x500")

        columns = ("Process", "PID", "Remote IP", "Remote Port", "Status")
        self.tree = ttk.Treeview(root, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=170)

        self.tree.pack(fill="both", expand=True)

        self.seen = set()
        self.running = True

        threading.Thread(target=self.monitor, daemon=True).start()

    def monitor(self):
        while self.running:
            try:
                for conn in psutil.net_connections(kind="inet"):
                    if not conn.raddr:
                        continue

                    key = (
                        conn.pid,
                        conn.raddr.ip,
                        conn.raddr.port,
                        conn.status
                    )

                    if key in self.seen:
                        continue

                    self.seen.add(key)

                    try:
                        pname = psutil.Process(conn.pid).name()
                    except:
                        pname = "Unknown"

                    self.root.after(
                        0,
                        lambda p=pname,
                               pid=conn.pid,
                               ip=conn.raddr.ip,
                               port=conn.raddr.port,
                               st=conn.status:
                        self.tree.insert(
                            "",
                            "end",
                            values=(p, pid, ip, port, st)
                        )
                    )

            except Exception as e:
                print(e)

            time.sleep(1)

root = tk.Tk()
app = NetworkMonitor(root)
root.mainloop()