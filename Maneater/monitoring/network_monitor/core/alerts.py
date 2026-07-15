"""
alerts.py

Tracks daily upload/download usage and fires alerts
when configured thresholds are exceeded.

Usage:
    from core.alerts import get_alerts, check_thresholds
    check_thresholds(session)   # call this on every refresh
    alerts = get_alerts()       # returns list of active alerts
"""

from datetime import date
from threading import Lock
from time import time

from utils.config import SETTINGS

MB = 1024 * 1024


# -------------------------------------------------------
# Alert store
# -------------------------------------------------------

_lock = Lock()

# Each alert is a dict:
#   { "type": "upload"|"download", "message": str, "timestamp": float }
_alerts = []

# Track which thresholds have already fired today so we
# don't spam the same alert on every packet.
_fired = set()

# The calendar date we're currently tracking.
# When this changes, we reset daily counters.
_current_day = date.today()

# Daily counters (bytes). Separate from Session totals
# because Session is cumulative for the entire run,
# whereas these reset at midnight.
_daily_upload = 0
_daily_download = 0


# -------------------------------------------------------
# Internal helpers
# -------------------------------------------------------

def _maybe_reset_day():
    """Reset daily counters if the calendar day has changed."""

    global _current_day, _daily_upload, _daily_download, _fired

    today = date.today()

    if today != _current_day:

        _current_day = today
        _daily_upload = 0
        _daily_download = 0
        _fired = set()

        _alerts.append({
            "type": "info",
            "message": f"Daily counters reset for {today.isoformat()}.",
            "timestamp": time(),
        })


def _fire(alert_type, message):
    """Add an alert if it hasn't already fired today."""

    if alert_type in _fired:
        return

    _fired.add(alert_type)

    _alerts.append({
        "type": alert_type,
        "message": message,
        "timestamp": time(),
    })

    # Keep the list bounded
    max_alerts = SETTINGS.get("max_alerts", 50)

    if len(_alerts) > max_alerts:
        _alerts.pop(0)


# -------------------------------------------------------
# Public API
# -------------------------------------------------------

def check_thresholds(session):
    """
    Call this periodically (e.g. every dashboard refresh).
    Compares session totals against daily limits and fires
    alerts when limits are crossed.
    """

    global _daily_upload, _daily_download

    with _lock:

        _maybe_reset_day()

        upload_limit   = SETTINGS.get("daily_upload_limit_mb",   0)
        download_limit = SETTINGS.get("daily_download_limit_mb", 0)

        _daily_upload   = session.total_upload
        _daily_download = session.total_download

        upload_mb   = _daily_upload   / MB
        download_mb = _daily_download / MB

        # -----------------------------------------------
        # Upload threshold checks
        # -----------------------------------------------

        if upload_limit > 0:

            # Warn at 80%
            if upload_mb >= upload_limit * 0.8:
                _fire(
                    "upload_warn",
                    f"Upload is at {upload_mb:.1f} MB — "
                    f"approaching your daily limit of {upload_limit} MB (80%)."
                )

            # Breach at 100%
            if upload_mb >= upload_limit:
                _fire(
                    "upload_limit",
                    f"Daily upload limit reached: "
                    f"{upload_mb:.1f} MB / {upload_limit} MB."
                )

        # -----------------------------------------------
        # Download threshold checks
        # -----------------------------------------------

        if download_limit > 0:

            # Warn at 80%
            if download_mb >= download_limit * 0.8:
                _fire(
                    "download_warn",
                    f"Download is at {download_mb:.1f} MB — "
                    f"approaching your daily limit of {download_limit} MB (80%)."
                )

            # Breach at 100%
            if download_mb >= download_limit:
                _fire(
                    "download_limit",
                    f"Daily download limit reached: "
                    f"{download_mb:.1f} MB / {download_limit} MB."
                )


def get_alerts():
    """Return all alerts, newest first."""

    with _lock:
        return list(reversed(_alerts))


def get_daily_usage():
    """Return current daily upload/download in bytes."""

    with _lock:

        return {
            "upload":   _daily_upload,
            "download": _daily_download,
            "day":      _current_day.isoformat(),
        }


def clear_alerts():
    """Manually clear all alerts (e.g. from a UI button)."""

    with _lock:
        _alerts.clear()