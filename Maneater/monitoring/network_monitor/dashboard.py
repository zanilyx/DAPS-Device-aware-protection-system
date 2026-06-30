"""
dashboard.py

Live terminal dashboard using Rich.
"""

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from statistics import (
    snapshot,
    calculate_speeds,
    format_bytes
)

console = Console()


# ----------------------------------------
# Status Color
# ----------------------------------------

def status_text(status):

    if status == "WHITELIST":
        return "[green]WHITELIST[/green]"

    if status == "BLACKLIST":
        return "[red]BLACKLIST[/red]"

    return "[yellow]UNKNOWN[/yellow]"


# ----------------------------------------
# Summary Panel
# ----------------------------------------

def build_summary(data):

    session = data["session_time"]

    hrs = session // 3600
    mins = (session % 3600) // 60
    secs = session % 60

    body = f"""

Session Time : {hrs:02}:{mins:02}:{secs:02}

Packets      : {data['total_packets']}

Unique IPs   : {data['unique_ips']}

Upload       : {format_bytes(data['total_upload'])}

Download     : {format_bytes(data['total_download'])}

Upload Speed : {format_bytes(data['upload_speed'])}/s

Download Spd : {format_bytes(data['download_speed'])}/s

"""

    return Panel(body, title="Session")


# ----------------------------------------
# Traffic Table
# ----------------------------------------

def build_table(data):

    table = Table(expand=True)

    table.add_column("Status")
    table.add_column("Remote IP")
    table.add_column("Upload", justify="right")
    table.add_column("Download", justify="right")
    table.add_column("Packets", justify="right")
    table.add_column("Protocols")
    table.add_column("Ports")

    rows = sorted(
        data["traffic"].items(),
        key=lambda item: item[1]["upload"],
        reverse=True
    )

    for ip, info in rows:

        protocols = ", ".join(sorted(info["protocols"]))

        ports = ", ".join(
            str(x)
            for x in sorted(info["ports"])
        )

        table.add_row(

            status_text(info["status"]),

            ip,

            format_bytes(info["upload"]),

            format_bytes(info["download"]),

            str(info["packets"]),

            protocols,

            ports

        )

    return table


# ----------------------------------------
# Footer
# ----------------------------------------

def build_footer():

    return Panel(
        Text(
            "Monitoring... Press CTRL+C to quit",
            justify="center"
        )
    )


# ----------------------------------------
# Layout
# ----------------------------------------

def create_layout():

    layout = Layout()

    layout.split_column(

        Layout(name="summary", size=13),

        Layout(name="table"),

        Layout(name="footer", size=3)

    )

    return layout


# ----------------------------------------
# Dashboard
# ----------------------------------------

def start_dashboard():

    layout = create_layout()

    with Live(

        layout,

        refresh_per_second=2,

        console=console

    ):

        while True:

            calculate_speeds()

            data = snapshot()

            layout["summary"].update(

                build_summary(data)

            )

            layout["table"].update(

                build_table(data)

            )

            layout["footer"].update(

                build_footer()

            )