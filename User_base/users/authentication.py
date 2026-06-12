import hashlib
import sqlite3
import os
from pathlib import Path

# 1. Find the directory where this script lives
current_dir = Path(__file__).resolve().parent.parent

# 2. Go up one or more levels to find your project root
# (If your script is inside /Main/, .parent is the root directory)
project_root = current_dir.parent

# 3. Target the 'database' folder at the root level
DB_NAME = os.path.join(project_root, "database", "users.db")


def hash_password(password: str) -> str:
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_user(username: str, password_raw: str) -> dict | None:
    """Verifies credentials by hashing input and comparing it to the stored hash.

    Returns user data dict if successful, else None.
    """
    hashed_input = hash_password(password_raw)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, role, department FROM users WHERE username = ? AND password_hash = ?",
        (username, hashed_input),
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return {"id": user[0], "username": user[1], "role": user[2], "department": user[3]}
    return None


if __name__ == "__main__":
    # Quick login test
    user_session = verify_user("test_user", "secure_pass123")
    print("Login status:", "Success" if user_session else "Failed")