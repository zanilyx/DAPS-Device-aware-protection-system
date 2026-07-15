"""
capture.py

Starts and stops packet capture.
Uses Scapy + Npcap (Windows)

packet_callback does the absolute minimum (queue push) so the
capture thread is never blocked. A worker thread does all parsing.
"""

import queue
from threading import Lock, Thread

from scapy.all import AsyncSniffer

from core.interface import get_capture_interface
from core.parser import parse_packet

_sniffer      = None
_running      = False
_lock         = Lock()
_worker_thread = None
_packet_queue  = queue.Queue(maxsize=20000)
_dropped_count = 0


def packet_callback(pkt):

    global _dropped_count

    try:
        _packet_queue.put_nowait(pkt)
    except queue.Full:
        _dropped_count += 1


def _worker_loop():

    while True:

        pkt = _packet_queue.get()

        if pkt is None:
            break

        try:
            parse_packet(pkt)
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            _packet_queue.task_done()


def start_capture():

    global _sniffer, _running, _worker_thread, _dropped_count

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

    global _sniffer, _running, _worker_thread

    with _lock:

        if not _running:
            return

        try:
            _sniffer.stop()
        except Exception:
            pass

        _packet_queue.join()
        _packet_queue.put(None)

        if _worker_thread:
            _worker_thread.join(timeout=5)

        if _dropped_count:
            print(
                f"Warning: dropped {_dropped_count} packets "
                f"(queue full — processing couldn't keep up)."
            )

        _running = False


def is_running():
    return _running


def dropped_packets():
    return _dropped_count