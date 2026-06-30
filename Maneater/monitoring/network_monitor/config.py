from pathlib import Path

# -----------------------------
# Paths
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent

WHITELIST_FILE = BASE_DIR / "whitelist.txt"
BLACKLIST_FILE = BASE_DIR / "blacklist.txt"

LOG_DIRECTORY = BASE_DIR / "logs"
LOG_DIRECTORY.mkdir(exist_ok=True)

REFRESH_RATE = 1          # seconds

PROMISCUOUS_MODE = True

# Alert when upload exceeds this amount
UPLOAD_ALERT_MB = 50

# Ignore localhost traffic
IGNORE_LOCALHOST = True


# -----------------------------
# Load IP Lists
# -----------------------------

def load_ip_file(file_path):

    ips = set()

    if not file_path.exists():
        return ips

    with open(file_path, "r") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            ips.add(line)

    return ips


WHITELIST = load_ip_file(WHITELIST_FILE)
BLACKLIST = load_ip_file(BLACKLIST_FILE)