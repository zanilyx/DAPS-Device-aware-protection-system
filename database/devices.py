import sqlite3

DB_NAME = "devices.db"


def create_devices_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT UNIQUE,
        device_type TEXT,
        hostname TEXT,
        mac_address TEXT,
        ip_address TEXT,
        owner TEXT,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_devices_table()
    print("Devices table created.")