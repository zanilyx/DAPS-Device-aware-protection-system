import sqlite3
import os

from users import create_users_table

DB_TABLES = {
    "users.db": ["users"]
}

create_users_table()
    
    # Fill Users
with sqlite3.connect("users.db") as conn:
    conn.execute("INSERT OR IGNORE INTO users (username, email, password_hash, role, department) VALUES ('admin', 'admin@test.com', 'hash123', 'admin', 'IT')")
