import sys

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
)


# ---------------- LOGIN PAGE ----------------

class LoginPage(QWidget):

    login_success = Signal(dict)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("LOGIN PAGE")

        login_btn = QPushButton("Login")

        login_btn.clicked.connect(self.fake_login)

        layout.addWidget(title)
        layout.addWidget(login_btn)

    def fake_login(self):

        user_data = {
            "username": "admin",
            "email": "admin@test.com",
            "role": "admin",
        }

        self.login_success.emit(user_data)


# ---------------- HOME PAGE ----------------

class HomePage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.label = QLabel("Home")

        layout.addWidget(self.label)

    def set_user(self, user):

        self.label.setText(
            f"""
Username: {user['username']}
Email: {user['email']}
Role: {user['role']}
"""
        )


# ---------------- LOGS PAGE ----------------

class LogsPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("Logs Page")
        )


# ---------------- MONITOR PAGE ----------------

class MonitorPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("Monitor Page")
        )


# ---------------- HEADER ----------------

class Header(QWidget):

    page_requested = Signal(str)

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        # PFP Placeholder
        pfp = QLabel("👤")

        btn_home = QPushButton("Home")
        btn_logs = QPushButton("Logs")
        btn_monitor = QPushButton("Monitor")

        btn_home.clicked.connect(
            lambda: self.page_requested.emit("home")
        )

        btn_logs.clicked.connect(
            lambda: self.page_requested.emit("logs")
        )

        btn_monitor.clicked.connect(
            lambda: self.page_requested.emit("monitor")
        )

        layout.addWidget(pfp)

        layout.addStretch()

        layout.addWidget(btn_home)
        layout.addWidget(btn_logs)
        layout.addWidget(btn_monitor)


# ---------------- DASHBOARD SHELL ----------------

class DashboardShell(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.header = Header()

        self.pages = QStackedWidget()

        self.home_page = HomePage()
        self.logs_page = LogsPage()
        self.monitor_page = MonitorPage()

        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.logs_page)
        self.pages.addWidget(self.monitor_page)

        layout.addWidget(self.header)
        layout.addWidget(self.pages)

        self.header.page_requested.connect(
            self.change_page
        )

    def change_page(self, page):

        if page == "home":
            self.pages.setCurrentWidget(
                self.home_page
            )

        elif page == "logs":
            self.pages.setCurrentWidget(
                self.logs_page
            )

        elif page == "monitor":
            self.pages.setCurrentWidget(
                self.monitor_page
            )


# ---------------- MAIN APP ----------------

class MainApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Universal GUI")

        self.resize(1000, 700)

        self.stack = QStackedWidget()

        self.setCentralWidget(self.stack)

        self.login_page = LoginPage()

        self.dashboard = DashboardShell()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.dashboard)

        self.login_page.login_success.connect(
            self.login_complete
        )

    def login_complete(self, user_data):

        self.dashboard.home_page.set_user(
            user_data
        )

        self.stack.setCurrentWidget(
            self.dashboard
        )


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainApp()
    window.show()

    sys.exit(app.exec())