"""
capture.py

Starts and stops packet capture.

Uses Scapy + Npcap (Windows)

The Scapy sniffer callback (packet_callback) runs in Npcap's capture
thread. If that callback does real work (parsing, flow lookups, locks)
it can't keep up with high packet rates, and the OS-level capture
buffer fills up and silently drops packets -- you lose traffic with
no error at all.

To avoid that, packet_callback does the absolute minimum: push the
raw packet onto a queue and return immediately. A separate worker
thread drains the queue and does the actual parsing/flow updates,
so the capture thread is always free to keep grabbing packets.
"""

import queue
from threading import Lock, Thread

from scapy.all import AsyncSniffer

from core.interface import get_capture_interface
from core.parser import parse_packet

_sniffer = None
_running = False
_lock = Lock()

_worker_thread = None

# Bounded so a runaway backlog doesn't eat unlimited memory, but
# large enough to absorb bursts. Tune if you still see drops.
_packet_queue = queue.Queue(maxsize=20000)

_dropped_count = 0


def packet_callback(pkt):
    """
    Called directly by Npcap/Scapy's capture thread.
    Must be as fast as possible -- no parsing here.
    """

    global _dropped_count

    try:
        _packet_queue.put_nowait(pkt)

    except queue.Full:
        # Queue is saturated -- processing can't keep up.
        # Drop the packet rather than blocking the capture
        # thread (blocking here would cause Npcap to drop
        # packets anyway, just less visibly).
        _dropped_count += 1


def _worker_loop():
    """
    Runs in its own thread. Pulls packets off the queue and
    does the real parsing/flow-tracking work, away from the
    time-sensitive capture thread.
    """

    while True:

        pkt = _packet_queue.get()

        if pkt is None:
            # Sentinel value used to stop the worker thread.
            break

        try:
            parse_packet(pkt)

        except Exception:
            import traceback
            traceback.print_exc()

        finally:
            _packet_queue.task_done()


def start_capture():

    global _sniffer
    global _running
    global _worker_thread
    global _dropped_count

    with _lock:

        if _running:
            return

        _dropped_count = 0

        iface = get_capture_interface()

        print(f"Capturing on: {iface}")

        _worker_thread = Thread(target=_worker_loop, daemon=True)
        _worker_thread.start()

        _sniffer = AsyncSniffer(

            iface=iface,

            prn=packet_callback,

            store=False,

            filter="ip or ip6"

        )

        _sniffer.start()

        _running = True


def stop_capture():

    global _sniffer
    global _running
    global _worker_thread

    with _lock:

        if not _running:
            return

        try:

            _sniffer.stop()

        except Exception:
            pass

        # Let the worker drain whatever's left in the queue,
        # then tell it to exit.
        _packet_queue.join()
        _packet_queue.put(None)

        if _worker_thread:
            _worker_thread.join(timeout=5)

        if _dropped_count:
            print(
                f"Warning: dropped {_dropped_count} packets "
                f"(processing couldn't keep up). Consider "
                f"increasing the queue size if this is high."
            )

        _running = False


def is_running():

    return _running


def dropped_packets():
    """
    Number of packets dropped because the processing queue
    was full. Should stay at 0 -- if this climbs during heavy
    traffic, the worker thread (i.e. parse_packet/flow tracking)
    is the bottleneck and needs optimizing, or the queue needs
    to be larger.
    """

    return _dropped_count