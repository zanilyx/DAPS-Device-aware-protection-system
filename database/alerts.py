import sqlite3

DB_NAME = "alerts.db"


def create_alerts_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        severity TEXT,
        category TEXT,
        description TEXT,
        resolved INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_alerts_table()
    print("Alerts table created.")