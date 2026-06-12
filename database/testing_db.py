import sqlite3
import os
from alerts import create_alerts_table
from devices import create_devices_table
from files import create_files_table
from logs import create_logs_table
from users import create_users_table

DB_TABLES = {
    "alerts.db": ["alerts"],
    "devices.db": ["devices"],
    "files.db": ["files"],
    "logs.db": ["audit_logs", "usb_logs"],
    "users.db": ["users"]
}

def fill_data():
    # Ensure tables exist
    create_alerts_table()
    create_devices_table()
    create_files_table()
    create_logs_table()
    create_users_table()
    
    # Fill Users
    with sqlite3.connect("users.db") as conn:
        conn.execute("INSERT OR IGNORE INTO users (username, email, password_hash, role, department) VALUES ('admin', 'admin@test.com', 'hash123', 'admin', 'IT')")
        conn.execute("INSERT OR IGNORE INTO users (username, email, password_hash, role, department) VALUES ('user1', 'user1@test.com', 'hash456', 'user', 'HR')")

    # Fill Devices
    with sqlite3.connect("devices.db") as conn:
        conn.execute("INSERT OR IGNORE INTO devices (device_id, device_type, hostname, mac_address, ip_address, owner) VALUES ('DEV001', 'Laptop', 'LT-ADMIN', '00:11:22:33:44:55', '192.168.1.50', 'admin')")

    # Fill Files
    with sqlite3.connect("files.db") as conn:
        conn.execute("INSERT OR IGNORE INTO files (file_id, filename, path, classification, department, role, access_type, encryption_status, owner) VALUES ('FILE001', 'confidential.doc', '/docs/confidential.doc', 'Secret', 'HR', 'manager', 'read', 'encrypted', 'user1')")

    # Fill Logs
    with sqlite3.connect("logs.db") as conn:
        conn.execute("INSERT INTO audit_logs (username, device_id, file_id, action, details) VALUES ('admin', 'DEV001', 'FILE001', 'READ', 'Accessed file successfully')")
        conn.execute("INSERT OR IGNORE INTO usb_logs (device_id, username, USB_Type) VALUES ('DEV001', 'admin', 'Storage')")

    # Fill Alerts
    with sqlite3.connect("alerts.db") as conn:
        conn.execute("INSERT INTO alerts (severity, category, description) VALUES ('HIGH', 'Unauthorized Access', 'User tried accessing restricted file')")
    
    print("Dummy data filled.")

def reset_data():
    for db, tables in DB_TABLES.items():
        if os.path.exists(db):
            with sqlite3.connect(db) as conn:
                for table in tables:
                    try:
                        conn.execute(f"DELETE FROM {table}")
                        conn.execute("DELETE FROM sqlite_sequence WHERE name=?", (table,))
                    except sqlite3.OperationalError:
                        pass
    print("Databases reset/cleared.")

if __name__ == "__main__":
    choice = input("Enter 'fill' to add dummy data or 'reset' to clear it: ").strip().lower()
    if choice == 'fill':
        fill_data()
    elif choice == 'reset':
        reset_data()
    else:
        print("Invalid option.")