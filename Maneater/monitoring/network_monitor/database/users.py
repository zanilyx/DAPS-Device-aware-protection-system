"""
users.py

User authentication and authorization database.
Stores admin and manager credentials with role-based access control.
"""

import sqlite3
from pathlib import Path
from hashlib import sha256
from typing import Optional, Tuple
import json

# Database path
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "users.db"


def init_db():
    """Initialize the users database with schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'manager')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    """)
    
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return sha256(password.encode()).hexdigest()


def add_user(username: str, password: str, role: str = "manager") -> bool:
    """
    Add a new user to the database.
    
    Args:
        username: Username
        password: Plain text password (will be hashed)
        role: 'admin' or 'manager' (default: 'manager')
    
    Returns:
        True if successful, False if user already exists
    """
    if role not in ("admin", "manager"):
        raise ValueError("Role must be 'admin' or 'manager'")
    
    init_db()
    
    password_hash = hash_password(password)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, role)
            VALUES (?, ?, ?)
        """, (username, password_hash, role))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def authenticate(username: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Authenticate a user.
    
    Args:
        username: Username
        password: Plain text password
    
    Returns:
        Tuple of (is_authenticated, role)
        Returns (False, None) if authentication fails
    """
    init_db()
    
    password_hash = hash_password(password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT role FROM users
        WHERE username = ? AND password_hash = ? AND active = 1
    """, (username, password_hash))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return True, result[0]
    
    return False, None


def get_user(username: str) -> Optional[dict]:
    """Get user information."""
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, role, active FROM users
        WHERE username = ?
    """, (username,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            "id": result[0],
            "username": result[1],
            "role": result[2],
            "active": result[3]
        }
    
    return None


def delete_user(username: str) -> bool:
    """Delete a user from the database."""
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    
    return affected > 0


def list_users() -> list:
    """List all active users."""
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, role, created_at FROM users
        WHERE active = 1
        ORDER BY created_at DESC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return [
        {
            "username": row[0],
            "role": row[1],
            "created_at": row[2]
        }
        for row in results
    ]
