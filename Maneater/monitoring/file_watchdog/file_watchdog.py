import sys
import time
import threading
import sqlite3
import os
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ==========================================================
# PATHS
# ==========================================================
# This file lives at: Maneater/monitoring/file_watchdog/file_watchdog.py
# Project root (contains "database/") is four levels up.

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

FILES_DB = ROOT_DIR / "database" / "files.db"

# Must match COMPANY_DB in Filecrypter/encryption/encrypt.py exactly
COMPANY_DB = r"C:\Piyush\Projects\CCNCS\Files\code\Company DB"

alerts_dir = ROOT_DIR / "Maneater" / "alerts"
if str(alerts_dir) not in sys.path:
    sys.path.insert(0, str(alerts_dir))

from alert_manager import raise_alert, Severity

# Grace period before flagging a newly-appeared file as "unregistered".
# encrypt_file() moves the .daps into Company DB BEFORE it writes the
# files.db row, so a legitimate encryption briefly looks unregistered.
# This delay lets that registration step catch up before we alert.
REGISTRATION_GRACE_SECONDS = 3.0


# ==========================================================
# DB LOOKUPS
# ==========================================================

def _query_files_db(query, params):
    conn = sqlite3.connect(FILES_DB)
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        conn.close()


def is_registered_file(path: str) -> bool:
    row = _query_files_db("SELECT file_id FROM files WHERE path=?", (path,))
    return row is not None


def get_filename_for_path(path: str):
    row = _query_files_db("SELECT filename FROM files WHERE path=?", (path,))
    return row[0] if row else None


# ==========================================================
# EVENT HANDLER
# ==========================================================

class CompanyDBHandler(FileSystemEventHandler):
    """
    Watches Company DB for changes that didn't come through the app's
    normal encrypt/decrypt flow — deleted, modified, moved, or unexpected
    new files.
    """

    def on_created(self, event):
        if event.is_directory:
            return
        self._check_registration_later(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return

        old_filename = get_filename_for_path(event.src_path)
        if old_filename:
            raise_alert(
                source="FILE_WATCHDOG",
                severity=Severity.CRITICAL,
                title="Protected file moved or renamed",
                message=f"{old_filename} was moved/renamed outside the application "
                        f"(new path: {event.dest_path})."
            )

        # the destination is also a "new" path worth checking
        self._check_registration_later(event.dest_path)

    def on_deleted(self, event):
        if event.is_directory:
            return

        filename = get_filename_for_path(event.src_path)
        if filename:
            raise_alert(
                source="FILE_WATCHDOG",
                severity=Severity.CRITICAL,
                title="Protected file deleted",
                message=f"{filename} was deleted from Company DB outside the application."
            )

    def on_modified(self, event):
        if event.is_directory:
            return

        filename = get_filename_for_path(event.src_path)
        if filename:
            raise_alert(
                source="FILE_WATCHDOG",
                severity=Severity.WARNING,
                title="Protected file modified",
                message=f"{filename} was modified outside the application. "
                        f"Its encrypted contents may now be corrupted or tampered with."
            )

    def _check_registration_later(self, path: str):
        # Delayed re-check instead of an immediate alert, so a file that's
        # mid-encryption (moved into place, about to be registered) doesn't
        # get flagged as unauthorized.
        timer = threading.Timer(
            REGISTRATION_GRACE_SECONDS,
            self._check_registration_now,
            args=(path,)
        )
        timer.daemon = True
        timer.start()

    def _check_registration_now(self, path: str):
        if not os.path.exists(path):
            return  # already gone, nothing to flag

        if is_registered_file(path):
            return  # legitimate — the app registered it in time

        raise_alert(
            source="FILE_WATCHDOG",
            severity=Severity.WARNING,
            title="Unregistered file in Company DB",
            message=f"{path} exists in protected storage but is not registered in files.db."
        )


# ==========================================================
# ENTRY POINT
# ==========================================================

def start_watchdog(stop_event=None):
    os.makedirs(COMPANY_DB, exist_ok=True)

    handler = CompanyDBHandler()
    observer = Observer()
    observer.schedule(handler, COMPANY_DB, recursive=True)
    observer.start()

    print(f"File watchdog started. Watching: {COMPANY_DB}")

    try:
        while stop_event is None or not stop_event.is_set():
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
        print("File watchdog stopped.")


if __name__ == "__main__":
    try:
        start_watchdog()
    except KeyboardInterrupt:
        print("\nFile watchdog stopped by user.")