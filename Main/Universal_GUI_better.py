from PySide6.QtCore import Qt, Signal, QTimer
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
from PySide6.QtGui import (
    QPainter,
    QColor,
    QFont
)
from PySide6.QtCore import Qt
import sys
import threading
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
from GUI_modules.Login_page_GUI import LoginPage
from GUI_modules.Home_GUI import HomePage

# ---------------- USB MONITOR (background) ----------------

from Maneater.monitoring.usb_monitor.usb_monitor import monitor as run_usb_monitor

# ---------------- LOGIN PAGE ----------------

class Login_Page(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login Page")
        self.resize(400, 300)

        # Main stack navigation matrix
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize pages
        self.login_page = LoginPage()
        self.home_page = HomePage()

        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.home_page)

        # Connect login success signal to the window router
        self.login_page.login_success.connect(self.navigate_to_dashboard)

    def navigate_to_dashboard(self, user_data: dict):
        """Switches view to dashboard and passes along user details."""
        self.home_page.set_user_info(user_data)
        self.stacked_widget.setCurrentWidget(self.home_page)



# ---------------- MONITOR PAGE ----------------

import psutil

MON_BG_SURFACE = "#1C2E42"
MON_BORDER = "#2A4059"
MON_TEXT_PRI = "#F0F4F8"
MON_TEXT_SEC = "#8FA8BF"
MON_ACCENT = "#4A9EBF"


def _format_speed(bytes_per_sec: float) -> str:
    if bytes_per_sec >= 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
    return f"{bytes_per_sec / 1024:.1f} KB/s"


class StatCard(QWidget):

    def __init__(self, title: str):
        super().__init__()
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {MON_BG_SURFACE};
                border: 1px solid {MON_BORDER};
                border-radius: 10px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        title_label = QLabel(title.upper())
        title_label.setStyleSheet(f"""
            color: {MON_TEXT_SEC}; font-size: 10px; font-weight: 600;
            letter-spacing: 1px; background: transparent; border: none;
        """)

        self.value_label = QLabel("—")
        self.value_label.setStyleSheet(f"""
            color: {MON_TEXT_PRI}; font-size: 22px; font-weight: 700;
            background: transparent; border: none;
        """)

        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

    def set_value(self, text: str):
        self.value_label.setText(text)


class MonitorPage(QWidget):

    def __init__(self):
        super().__init__()

        self.setStyleSheet("background: transparent;")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 32, 40, 40)
        outer.setSpacing(20)

        heading = QLabel("System & Network Monitor")
        heading.setStyleSheet(f"""
            color: {MON_TEXT_PRI}; font-size: 22px; font-weight: 700;
            background: transparent; border: none;
        """)
        outer.addWidget(heading)

        # ── network row ──
        net_row = QHBoxLayout()
        net_row.setSpacing(16)

        self.download_card = StatCard("Download Speed")
        self.upload_card = StatCard("Upload Speed")

        net_row.addWidget(self.download_card)
        net_row.addWidget(self.upload_card)

        outer.addLayout(net_row)

        # ── system resource row ──
        sys_row = QHBoxLayout()
        sys_row.setSpacing(16)

        self.cpu_card = StatCard("CPU Usage")
        self.ram_card = StatCard("RAM Usage")
        self.disk_card = StatCard("Disk Usage")

        sys_row.addWidget(self.cpu_card)
        sys_row.addWidget(self.ram_card)
        sys_row.addWidget(self.disk_card)

        outer.addLayout(sys_row)

        outer.addStretch()

        # baseline counters for speed calculation
        counters = psutil.net_io_counters()
        self._last_bytes_sent = counters.bytes_sent
        self._last_bytes_recv = counters.bytes_recv

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1000)  # poll every second

    def _refresh(self):
        # network speed (delta over ~1s interval)
        counters = psutil.net_io_counters()

        sent_delta = counters.bytes_sent - self._last_bytes_sent
        recv_delta = counters.bytes_recv - self._last_bytes_recv

        self._last_bytes_sent = counters.bytes_sent
        self._last_bytes_recv = counters.bytes_recv

        self.upload_card.set_value(_format_speed(sent_delta))
        self.download_card.set_value(_format_speed(recv_delta))

        # system resource usage
        cpu_percent = psutil.cpu_percent(interval=None)
        ram_percent = psutil.virtual_memory().percent
        disk_percent = psutil.disk_usage(Path.home().anchor).percent

        self.cpu_card.set_value(f"{cpu_percent:.0f}%")
        self.ram_card.set_value(f"{ram_percent:.0f}%")
        self.disk_card.set_value(f"{disk_percent:.0f}%")

    def showEvent(self, event):
        # reset psutil's internal cpu_percent sampling window each time the
        # page becomes visible so the first reading after switching tabs
        # isn't stale
        psutil.cpu_percent(interval=None)
        super().showEvent(event)

# ---------------- Avatar ----------------

class Avatar(QWidget):

    def __init__(self, username="?", size=35):
        super().__init__()

        self.username = username

        self.avatar_size = size

        self.setFixedSize(size, size)

    def set_username(self, username):

        self.username = username

        self.update()

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        # Teams-like blue
        painter.setBrush(
            QColor("#4A90E2")
        )

        painter.setPen(Qt.NoPen)

        rect = self.rect().adjusted(
    1,
    1,
    -1,
    -1
)

        painter.drawEllipse(rect)

        # Letter
        painter.setPen(Qt.white)

        font = QFont()

        font.setBold(True)

        font.setPixelSize(
            19
        )

        painter.setFont(font)

        letter = "?"

        if self.username:
            letter = self.username[0].upper()

        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            letter
        )
        
# ---------------- HEADER ----------------

class Header(QWidget):

    page_requested = Signal(str)
    logout_requested = Signal()

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.avatar = Avatar(
    username="?",
    size=35
)

        self.username_label = QLabel("Guest")

        btn_home = QPushButton("Home")
        btn_monitor = QPushButton("Monitor")
        btn_logout = QPushButton("Logout")

        btn_home.clicked.connect(
            lambda: self.page_requested.emit("home")
        )

        btn_monitor.clicked.connect(
            lambda: self.page_requested.emit("monitor")
        )

        btn_logout.clicked.connect(
            lambda: self.logout_requested.emit()
        )

        layout.addWidget(self.avatar)
        layout.addWidget(self.username_label)

        layout.addStretch()

        layout.addWidget(btn_home)
        layout.addWidget(btn_monitor)
        layout.addWidget(btn_logout)

    def set_user(self, username):

        self.avatar.set_username(
            username
        )

        self.username_label.setText(
            username
        )

              
# ---------------- DASHBOARD SHELL ----------------

class DashboardShell(QWidget):

    logout_requested = Signal()

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.header = Header()

        self.pages = QStackedWidget()

        self.home_page = HomePage()
        self.monitor_page = MonitorPage()

        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.monitor_page)

        layout.addWidget(self.header)
        layout.addWidget(self.pages)

        self.header.page_requested.connect(
            self.change_page
        )

        self.header.logout_requested.connect(
            self.logout_requested.emit
        )

    def set_user(self, user_data):

        username = user_data["username"]

        self.header.set_user(username)

        if hasattr(self.home_page, "set_user_info"):
            self.home_page.set_user_info(user_data)

    def change_page(self, page):

        if page == "home":

            self.pages.setCurrentWidget(
                self.home_page
            )

        elif page == "monitor":

            self.pages.setCurrentWidget(
                self.monitor_page
            )

# ---------------- MAIN APP ----------------

class MainApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DAPS")

        # Login screen fixed size
        self.setFixedSize(500, 350)

        self.stack = QStackedWidget()

        self.setCentralWidget(self.stack)

        self.login_page = LoginPage()

        self.dashboard = DashboardShell()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.dashboard)

        self.stack.setCurrentWidget(
            self.login_page
        )

        self.login_page.login_success.connect(
            self.login_complete
        )

        self.dashboard.logout_requested.connect(
            self.handle_logout
        )

        # ---------------- USB MONITOR (background) ----------------
        # Runs silently: no UI, all activity logged to logs.db via db_logger.
        self._usb_stop_event = threading.Event()
        self._usb_thread = threading.Thread(
            target=run_usb_monitor,
            args=(self._usb_stop_event,),
            daemon=True
        )
        self._usb_thread.start()

    def closeEvent(self, event):
        self._usb_stop_event.set()
        event.accept()

    def handle_logout(self):

        # clear any typed credentials so they aren't left sitting in the fields
        if hasattr(self.login_page, "username_input"):
            self.login_page.username_input.clear()
        if hasattr(self.login_page, "password_input"):
            self.login_page.password_input.clear()

        self.stack.setCurrentWidget(
            self.login_page
        )

        # lock window back down to login-screen size
        self.setMinimumSize(0, 0)
        self.setFixedSize(500, 350)

    def login_complete(self, user_data):

        self.dashboard.set_user(user_data)

        self.stack.setCurrentWidget(
            self.dashboard
        )

        # unlock resizing after login
        self.setMinimumSize(1000, 700)

        self.resize(1200, 800)

        self.showMaximized()

if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainApp()
    window.show()

    sys.exit(app.exec())