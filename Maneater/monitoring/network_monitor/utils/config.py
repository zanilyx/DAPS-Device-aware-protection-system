"""
config.py

Global configuration and application settings.
"""

from pathlib import Path
import json

# --------------------------------------------------
# Project Paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CORE_DIR = PROJECT_ROOT / "core"
UI_DIR = PROJECT_ROOT / "ui"
DATABASE_DIR = PROJECT_ROOT / "database"

EXPORT_DIR = PROJECT_ROOT / "exports"
LOG_DIR = PROJECT_ROOT / "logs"

WHITELIST_FILE = PROJECT_ROOT / "whitelist.txt"
BLACKLIST_FILE = PROJECT_ROOT / "blacklist.txt"

SETTINGS_FILE = PROJECT_ROOT / "settings.json"

EXPORT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# --------------------------------------------------
# Default Settings
# --------------------------------------------------

DEFAULT_SETTINGS = {

    "refresh_rate": 1,

    "capture_filter": "",

    "resolve_hostnames": False,

    "track_ipv6": True,

    "ignore_loopback": True,

    "max_events": 100,

    "max_alerts": 50,

    "upload_alert_mb": 50,

    "dashboard_sort": "upload"

}

# --------------------------------------------------
# Settings
# --------------------------------------------------

def load_settings():

    if not SETTINGS_FILE.exists():

        with open(SETTINGS_FILE, "w") as f:

            json.dump(
                DEFAULT_SETTINGS,
                f,
                indent=4
            )

        return DEFAULT_SETTINGS.copy()

    with open(SETTINGS_FILE, "r") as f:

        data = json.load(f)

    for key, value in DEFAULT_SETTINGS.items():

        if key not in data:
            data[key] = value

    return data


SETTINGS = load_settings()

# --------------------------------------------------
# IP Lists
# --------------------------------------------------

def load_ip_list(path):

    if not path.exists():
        return set()

    ips = set()

    with open(path) as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            ips.add(line)

    return ips


WHITELIST = load_ip_list(WHITELIST_FILE)

BLACKLIST = load_ip_list(BLACKLIST_FILE)