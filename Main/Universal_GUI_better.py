from PySide6.QtCore import Qt, Signal
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

# usb_monitor_dir = root_dir / "Maneater" / "monitoring"
# if str(usb_monitor_dir) not in sys.path:
#     sys.path.insert(0, str(usb_monitor_dir))

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

class MonitorPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        layout.addWidget(
            QLabel("Monitor Page")
        )

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

        btn_home.clicked.connect(
            lambda: self.page_requested.emit("home")
        )

        btn_monitor.clicked.connect(
            lambda: self.page_requested.emit("monitor")
        )

        layout.addWidget(self.avatar)
        layout.addWidget(self.username_label)

        layout.addStretch()

        layout.addWidget(btn_home)
        layout.addWidget(btn_monitor)

    def set_user(self, username):

        self.avatar.set_username(
            username
        )

        self.username_label.setText(
            username
        )

              
# ---------------- DASHBOARD SHELL ----------------

class DashboardShell(QWidget):

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