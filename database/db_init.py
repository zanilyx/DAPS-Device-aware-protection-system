from users import create_users_table
from devices import create_devices_table
from files import create_files_table
from logs import create_logs_table
from alerts import create_alerts_table


def initialize_all_databases():
    create_users_table()
    create_devices_table()
    create_files_table()
    create_logs_table()
    create_alerts_table()

    print("All databases initialized.")


if __name__ == "__main__":
    initialize_all_databases()