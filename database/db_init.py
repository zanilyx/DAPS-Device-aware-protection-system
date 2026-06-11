from users_db import create_users_table
from devices_db import create_devices_table
from files_db import create_files_table
from permissions_db import create_permissions_table
from logs_db import create_logs_table
from alerts_db import create_alerts_table


def initialize_all_databases():
    create_users_table()
    create_devices_table()
    create_files_table()
    create_permissions_table()
    create_logs_table()
    create_alerts_table()

    print("All databases initialized.")


if __name__ == "__main__":
    initialize_all_databases()