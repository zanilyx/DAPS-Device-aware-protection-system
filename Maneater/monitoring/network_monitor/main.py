"""
main.py

Entry point for the Network Monitor
"""

import sys
from rich.console import Console

from capture import start_capture
from dashboard import start_dashboard

console = Console()


def main():

    console.print("[bold cyan]====================================[/bold cyan]")
    console.print("[bold cyan]      Network Traffic Monitor[/bold cyan]")
    console.print("[bold cyan]====================================[/bold cyan]\n")

    console.print("[green][+] Starting packet capture...[/green]")

    start_capture()

    console.print("[green][+] Dashboard started.[/green]\n")

    try:
        start_dashboard()

    except KeyboardInterrupt:

        console.print("\n[yellow][!] Stopping monitor...[/yellow]")

        sys.exit(0)


if __name__ == "__main__":
    main()