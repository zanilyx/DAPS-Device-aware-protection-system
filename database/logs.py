import sqlite3

DB_NAME = "logs.db"


def create_logs_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        username TEXT,
        device_id TEXT,
        file_id TEXT,
        action TEXT,
        status TEXT,
        details TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usb_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        serial_number TEXT,
        action TEXT,
        username TEXT
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_logs_table()
    print("Logs tables created.")