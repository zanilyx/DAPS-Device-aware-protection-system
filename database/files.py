import sqlite3

DB_NAME = "files.db"


def create_files_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT UNIQUE,
        filename TEXT,
        path TEXT,
        classification TEXT,
        department TEXT,
        role TEXT,
        access_type TEXT,
        encryption_status TEXT,
        owner TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_files_table()
    print("Files table created.")