"""
dashboard.py

Live terminal dashboard.
"""

from time import sleep

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.flows import (
    get_session,
    top_flows
)

console = Console()


# -----------------------------------------------------
# Human-readable bytes
# -----------------------------------------------------

def human(size):

    value = float(size)

    units = [

        "B",
        "KB",
        "MB",
        "GB",
        "TB"

    ]

    for unit in units:

        if value < 1024:

            return f"{value:.2f} {unit}"

        value /= 1024

    return f"{value:.2f} PB"


# -----------------------------------------------------
# Session Panel
# -----------------------------------------------------

def build_summary():

    session = get_session()

    runtime = session.runtime

    h = runtime // 3600
    m = (runtime % 3600) // 60
    s = runtime % 60

    body = f"""
Runtime          : {h:02}:{m:02}:{s:02}

Total Upload     : {human(session.total_upload)}

Total Download   : {human(session.total_download)}

Packets          : {session.total_packets:,}

Flows            : {session.total_flows}

Unique IPs       : {session.unique_ips}
"""

    return Panel(
        body,
        title="Session",
        border_style="cyan"
    )


# -----------------------------------------------------
# Traffic Table
# -----------------------------------------------------

def build_table():

    table = Table(expand=True)

    table.add_column("Status", style="bold")
    table.add_column("Remote IP")
    table.add_column("Protocol")
    table.add_column("Upload", justify="right")
    table.add_column("Download", justify="right")
    table.add_column("Packets", justify="right")

    flows = top_flows(500)

    # ---------------------------------------------
    # Group flows that share the same remote IP +
    # protocol (e.g. multiple simultaneous downloads
    # from the same server on different ports) into
    # a single aggregated row.
    # ---------------------------------------------

    grouped = {}

    for flow in flows:

        # "Remote" is whichever side isn't local. Since
        # both upload and download flows are stored the
        # same way, fall back to dst_ip when we can't
        # tell (upload-heavy flows use dst as remote,
        # download-heavy flows use src as remote).
        if flow.download_bytes > flow.upload_bytes:
            remote = flow.src_ip
        else:
            remote = flow.dst_ip

        key = (remote, flow.protocol)

        if key not in grouped:

            grouped[key] = {
                "status": flow.status,
                "remote": remote,
                "protocol": flow.protocol,
                "upload": 0,
                "download": 0,
                "packets": 0,
            }

        entry = grouped[key]

        entry["upload"] += flow.upload_bytes
        entry["download"] += flow.download_bytes
        entry["packets"] += flow.upload_packets + flow.download_packets

        # If any contributing flow is blacklisted/whitelisted,
        # let that take priority over UNKNOWN.
        if flow.status in ("BLACKLIST", "WHITELIST"):
            entry["status"] = flow.status

    rows = sorted(
        grouped.values(),
        key=lambda e: e["upload"] + e["download"],
        reverse=True
    )[:100]

    for entry in rows:

        if entry["status"] == "BLACKLIST":
            status = "[red]BLACKLIST[/red]"

        elif entry["status"] == "WHITELIST":
            status = "[green]WHITELIST[/green]"

        else:
            status = "[yellow]UNKNOWN[/yellow]"

        table.add_row(

            status,

            entry["remote"],

            entry["protocol"],

            human(entry["upload"]),

            human(entry["download"]),

            str(entry["packets"])

        )

    return table


# -----------------------------------------------------
# Footer
# -----------------------------------------------------

def build_footer():

    return Panel(

        Text(

            "CTRL+C to exit",

            justify="center"

        ),

        border_style="green"

    )


# -----------------------------------------------------
# Layout
# -----------------------------------------------------

def build_layout():

    layout = Layout()

    layout.split_column(

        Layout(name="summary", size=10),

        Layout(name="table"),

        Layout(name="footer", size=3)

    )

    return layout


# -----------------------------------------------------
# Dashboard
# -----------------------------------------------------

def start_dashboard():

    layout = build_layout()

    with Live(

        layout,

        console=console,

        refresh_per_second=2,

        screen=True

    ):

        while True:

            layout["summary"].update(

                build_summary()

            )

            layout["table"].update(

                build_table()

            )

            layout["footer"].update(

                build_footer()

            )

            sleep(0.5)