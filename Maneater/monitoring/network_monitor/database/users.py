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

print(f"[Network Monitor Auth] Database path: {DB_PATH}")
print(f"[Network Monitor Auth] Database exists: {DB_PATH.exists()}")


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
    
    print(f"[Auth] Attempting login for user: {username}")
    print(f"[Auth] Password hash: {password_hash}")
    print(f"[Auth] DB Path: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # First, let's see what's in the database
        cursor.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,))
        db_result = cursor.fetchone()
        
        if db_result:
            db_username, db_hash, db_role = db_result
            print(f"[Auth] Found user: {db_username}")
            print(f"[Auth] DB hash: {db_hash}")
            print(f"[Auth] DB role: {db_role}")
            print(f"[Auth] Hash match: {password_hash == db_hash}")
            
            if password_hash == db_hash and db_role in ('admin', 'manager'):
                print(f"[Auth] Authentication SUCCESS")
                conn.close()
                return True, db_role
            else:
                print(f"[Auth] Authentication FAILED - hash or role mismatch")
        else:
            print(f"[Auth] User not found in database")
        
        conn.close()
        return False, None
        
    except Exception as e:
        print(f"[Auth] Authentication error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def get_user(username: str) -> Optional[dict]:
    """Get user information from the existing database."""
    try:
        conn = sqlite3.connect(str(DB_PATH))
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
        print(f"[Auth] Error fetching user: {e}")
        return None
