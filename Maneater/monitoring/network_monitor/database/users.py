"""
users.py

User authentication and authorization for network monitor.
Uses the existing users.db from the main database directory.
"""

import sqlite3
from pathlib import Path
from hashlib import sha256
from typing import Optional, Tuple

# Path to the existing users.db at project root
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT_DIR / "database" / "users.db"


def authenticate(username: str, password: str) -> Tuple[bool, Optional[str]]:
    """
    Authenticate a user against the existing users database.
    
    Args:
        username: Username
        password: Plain text password
    
    Returns:
        Tuple of (is_authenticated, role)
        Returns (False, None) if authentication fails or user is not admin/manager
    """
    password_hash = sha256(password.encode()).hexdigest()
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT role FROM users
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            role = result[0]
            # Only admin or manager can access network monitor
            if role in ('admin', 'manager'):
                return True, role
        
        return False, None
    except Exception as e:
        print(f"Authentication error: {e}")
        return False, None


def get_user(username: str) -> Optional[dict]:
    """Get user information from the existing database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, role, department
            FROM users
            WHERE username = ?
        """, (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "id": result[0],
                "username": result[1],
                "role": result[2],
                "department": result[3]
            }
        
        return None
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None
