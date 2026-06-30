"""
main.py

Network Monitor Entry Point
"""

import signal
import sys
from rich.console import Console

from core.capture import start_capture, stop_capture
from ui.dashboard import start_dashboard
from ui.webapp import start_web_dashboard
import threading

threading.Thread(target=start_web_dashboard, daemon=True).start()

console = Console()


_running = True


def shutdown(signum=None, frame=None):
    """
    Gracefully stop the monitor.
    """

    global _running

    if not _running:
        return

    _running = False

    console.print("\n[yellow]Stopping capture...[/yellow]")

    try:
        stop_capture()
    except Exception as e:
        console.print(f"[red]Capture stop error:[/red] {e}")

    console.print("[green]Monitor stopped.[/green]")

    sys.exit(0)


def banner():

    console.print()

    console.print(
        "[bold cyan]==============================================[/bold cyan]"
    )

    console.print(
        "[bold cyan]        NETWORK TRAFFIC MONITOR[/bold cyan]"
    )

    console.print(
        "[bold cyan]==============================================[/bold cyan]"
    )

    console.print()


def main():

    signal.signal(signal.SIGINT, shutdown)

    # Windows doesn't support SIGTERM in the same way,
    # but registering it doesn't hurt.
    try:
        signal.signal(signal.SIGTERM, shutdown)
    except Exception:
        pass

    banner()

    console.print("[green][1/2][/green] Starting packet capture...")
    start_capture()

    console.print("[green][2/2][/green] Starting dashboard...")

    start_dashboard()


if __name__ == "__main__":
    main()