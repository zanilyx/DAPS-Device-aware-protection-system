import hashlib
import os
import sqlite3

# Update this path if your users.db is in a different root folder!
DB_NAME = "users.db"


def hash_password(password: str) -> str:
    """Hashes a password using SHA-256 (outputs lowercase hex string)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def add_test_user(username, email, raw_password, role="user", department=None):
    # 1. Securely hash the plain-text password
    hashed_password = hash_password(raw_password)

    # 2. Connect to the SQLite database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # 3. Insert matching your exact column names
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, department)
            VALUES (?, ?, ?, ?, ?)
        """,
            (username, email, hashed_password, role, department),
        )

        conn.commit()
        print(f"Successfully created user '{username}'!")
        print(f"Stored Hash in DB: {hashed_password}")

    except sqlite3.IntegrityError:
        print(f"Error: Username '{username}' already exists in the database.")
    finally:
        conn.close()


if __name__ == "__main__":
    # Example: Creating your test user
    # This will hash 'hash123' into '673d190b758967621da243f06c350ce68be4276174dc886560239fea923d4a5a'
    add_test_user(
        username="test_user",
        email="test@example.com",
        raw_password="hash123",
        role="admin",  # You mentioned adding your own roles/permissions later
        department="IT",
    )