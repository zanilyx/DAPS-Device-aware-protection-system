import sqlite3

DB_NAME = "permissions.db"


def create_permissions_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permissions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT,
        device_id TEXT,
        access_type TEXT,
        granted_by TEXT,
        granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_permissions_table()
    print("Permissions table created.")