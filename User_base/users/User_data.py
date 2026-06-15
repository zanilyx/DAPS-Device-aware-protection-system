import sqlite3
import os
from pathlib import Path
from typing import Optional


# 1. Find the directory where this script lives
current_dir = Path(__file__).resolve().parent.parent

# 2. Go up one or more levels to find your project root
# (If your script is inside /Main/, .parent is the root directory)
project_root = current_dir.parent

# 3. Target the 'database' folder at the root level
DB_NAME = os.path.join(project_root, "database", "users.db")

def user_details(username: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, username, email, role, department
        FROM users
        WHERE username = ?
        """,
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    if user:
        return{
            "id": user[0],
            "username": user[1],
            "email": user[2],
            "role": user[3],
            "department": user[4]
        }

    return None

if __name__ == "__main__":
    print(user_details("admin"))