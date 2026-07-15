import sqlite3
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# ===================================================
# Storage location
# ===================================================
# This file lives at: Maneater/alerts/alert_manager.py
# Project root (contains "database/") is two levels up.

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
ALERTS_DB = ROOT_DIR / "database" / "alerts.db"


# ===================================================
# Severity levels
# ===================================================

class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# ===================================================
# Alert data object
# ===================================================

@dataclass
class Alert:
    source: str          # e.g. "USB", "NETWORK"
    severity: Severity
    title: str
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    alert_id: int = None  # set after DB insert


# ===================================================
# Alert Manager (singleton-style module functions)
# ===================================================

_lock = threading.Lock()
_listeners = []  # list of callables: fn(Alert) -> None


def _ensure_schema():
    conn = sqlite3.connect(ALERTS_DB)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT,
                severity TEXT,
                title TEXT,
                message TEXT,
                timestamp TEXT,
                acknowledged INTEGER DEFAULT 0
            )
        """)
        conn.commit()
    finally:
        conn.close()


_ensure_schema()


def register_listener(callback):
    """
    Register a callback to be invoked synchronously whenever a new
    alert is raised. callback receives a single Alert object.

    Example (future GUI wiring):
        alert_manager.register_listener(lambda a: show_toast(a.title, a.message))
    """
    with _lock:
        _listeners.append(callback)


def unregister_listener(callback):
    with _lock:
        if callback in _listeners:
            _listeners.remove(callback)


def raise_alert(source: str, severity: Severity, title: str, message: str) -> Alert:
    """
    Raise a new alert: persists it to alerts.db and notifies all
    registered listeners. Thread-safe — safe to call from any
    monitoring thread (USB, network, etc.).
    """
    alert = Alert(source=source, severity=severity, title=title, message=message)

    conn = sqlite3.connect(ALERTS_DB)
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO alerts (source, severity, title, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (alert.source, alert.severity.value, alert.title, alert.message, alert.timestamp))
        conn.commit()
        alert.alert_id = cur.lastrowid
    finally:
        conn.close()

    with _lock:
        listeners_snapshot = list(_listeners)

    for callback in listeners_snapshot:
        try:
            callback(alert)
        except Exception as e:
            print(f"[alert_manager] listener error: {e}")

    return alert


def get_recent_alerts(limit: int = 50, acknowledged: bool = None):
    """
    Fetch recent alerts for display in a future GUI alerts panel.
    acknowledged: None = all, True = only acknowledged, False = only unacknowledged
    """
    conn = sqlite3.connect(ALERTS_DB)
    try:
        cur = conn.cursor()
        if acknowledged is None:
            cur.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
        else:
            cur.execute(
                "SELECT * FROM alerts WHERE acknowledged=? ORDER BY id DESC LIMIT ?",
                (1 if acknowledged else 0, limit)
            )
        return cur.fetchall()
    finally:
        conn.close()


def acknowledge_alert(alert_id: int):
    conn = sqlite3.connect(ALERTS_DB)
    try:
        conn.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
        conn.commit()
    finally:
        conn.close()


def acknowledge_all_alerts():
    """Marks every currently-pending alert as acknowledged (used by GUI 'Clear All')."""
    conn = sqlite3.connect(ALERTS_DB)
    try:
        conn.execute("UPDATE alerts SET acknowledged=1 WHERE acknowledged=0")
        conn.commit()
    finally:
        conn.close()


# ===================================================
# Default listener: console print
# (temporary, until GUI registers its own listener)
# ===================================================

def _console_listener(alert: Alert):
    print(f"[ALERT][{alert.severity.value}][{alert.source}] {alert.title} — {alert.message}")


register_listener(_console_listener)