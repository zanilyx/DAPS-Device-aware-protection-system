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
    print(f"\n[AUTH] === Authentication Attempt ===")
    print(f"[AUTH] Username: {username}")
    print(f"[AUTH] Password input: {password}")
    
    password_hash = sha256(password.encode()).hexdigest()
    print(f"[AUTH] Hashed input password: {password_hash}")
    print(f"[AUTH] Database path: {DB_PATH}")
    print(f"[AUTH] Database exists: {DB_PATH.exists()}")
    
    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Get all users for debugging
        cursor.execute("SELECT username, password_hash, role FROM users")
        all_users = cursor.fetchall()
        print(f"[AUTH] Total users in database: {len(all_users)}")
        for u in all_users:
            print(f"[AUTH]   - User: {u[0]}, Role: {u[2]}")
        
        # Now check this specific user
        cursor.execute("""
            SELECT role FROM users
            WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        
        result = cursor.fetchone()
        
        if result:
            role = result[0]
            print(f"[AUTH] ✓ Match found! Role: {role}")
            # Only admin or manager can access network monitor
            if role in ('admin', 'manager'):
                print(f"[AUTH] ✓ Role '{role}' is authorized")
                conn.close()
                return True, role
            else:
                print(f"[AUTH] ✗ Role '{role}' is NOT authorized (need admin or manager)")
        else:
            # Check if user exists
            cursor.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (username,))
            user_result = cursor.fetchone()
            if user_result:
                print(f"[AUTH] User found but password hash doesn't match")
                print(f"[AUTH]   DB hash: {user_result[1]}")
                print(f"[AUTH]   Input hash: {password_hash}")
                print(f"[AUTH]   Match: {user_result[1] == password_hash}")
            else:
                print(f"[AUTH] ✗ User '{username}' not found in database")
        
        conn.close()
        return False, None
        
    except Exception as e:
        print(f"[AUTH] ✗ Authentication error: {e}")
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
        print(f"Error fetching user: {e}")
        return None
