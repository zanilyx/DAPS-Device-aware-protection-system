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
    QMessageBox,
)
from PySide6.QtGui import (
    QPainter,
    QColor,
    QFont
)
import sys
import threading
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
from GUI_modules.Login_page_GUI import LoginPage
from GUI_modules.Home_GUI import HomePage
from GUI_modules.Monitor_GUI import MonitorPage

# ---------------- USB MONITOR (background) ----------------

from Maneater.monitoring.usb_monitor.usb_monitor import monitor as run_usb_monitor

# ---------------- FILE WATCHDOG (background) ----------------

from Maneater.monitoring.file_watchdog.file_watchdog import start_watchdog as run_file_watchdog


# ---------------- GLOBAL THEMES ----------------
# Applied at the QApplication level so default-styled widgets — like the
# ones in Login_page_GUI.py, which we don't touch — pick up a matching
# professional look automatically via Qt's stylesheet cascade.

APP_THEMES = {
    "dark": dict(
        bg_deep="#0D1B2A",
        bg_surface="#1C2E42",
        accent="#4A9EBF",
        accent_dark="#2E7A9A",
        text_pri="#F0F4F8",
        text_sec="#8FA8BF",
        border="#2A4059",
    ),
    "light": dict(
        bg_deep="#EEF2F6",
        bg_surface="#FFFFFF",
        accent="#2E7A9A",
        accent_dark="#1F5C77",
        text_pri="#16232F",
        text_sec="#51697E",
        border="#D7E0E8",
    ),
}


def build_global_stylesheet(theme_name: str) -> str:
    t = APP_THEMES[theme_name]

    return f"""
        QWidget {{
            background-color: {t['bg_deep']};
            color: {t['text_pri']};
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }}

        QMainWindow {{
            background-color: {t['bg_deep']};
        }}

        QLabel {{
            background: transparent;
        }}

        QLineEdit {{
            background-color: {t['bg_surface']};
            border: 1px solid {t['border']};
            border-radius: 8px;
            padding: 10px 12px;
            color: {t['text_pri']};
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border: 1px solid {t['accent']};
        }}

        QPushButton {{
            background-color: {t['accent']};
            color: {'#0D1B2A' if theme_name == 'light' else t['text_pri']};
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{
            background-color: {t['accent_dark']};
        }}
        QPushButton:pressed {{
            background-color: {t['accent_dark']};
        }}

        QScrollArea {{
            border: none;
            background: transparent;
        }}

        QScrollBar:vertical {{
            background: {t['bg_deep']};
            width: 10px;
            border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {t['border']};
            border-radius: 5px;
            min-height: 24px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QMessageBox {{
            background-color: {t['bg_surface']};
        }}
    """


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

        painter.setBrush(
            QColor("#4A90E2")
        )

        painter.setPen(Qt.NoPen)

        rect = self.rect().adjusted(1, 1, -1, -1)

        painter.drawEllipse(rect)

        painter.setPen(Qt.white)

        font = QFont()
        font.setBold(True)
        font.setPixelSize(19)
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
    theme_toggle_requested = Signal()

    def __init__(self):
        super().__init__()

        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        self.avatar = Avatar(username="?", size=35)
        self.username_label = QLabel("Guest")
        self.username_label.setStyleSheet("font-weight: 600; font-size: 14px;")

        btn_home = QPushButton("Home")
        btn_monitor = QPushButton("Monitor")
        btn_logout = QPushButton("Logout")

        self.theme_btn = QPushButton("🌙")
        self.theme_btn.setFixedSize(32, 32)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("Toggle dark / light theme")
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 16px;
                font-size: 15px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 35);
            }
        """)

        btn_home.clicked.connect(lambda: self.page_requested.emit("home"))
        btn_monitor.clicked.connect(lambda: self.page_requested.emit("monitor"))
        btn_logout.clicked.connect(lambda: self.logout_requested.emit())
        self.theme_btn.clicked.connect(lambda: self.theme_toggle_requested.emit())

        layout.addWidget(self.avatar)
        layout.addWidget(self.username_label)

        layout.addStretch()

        layout.addWidget(btn_home)
        layout.addWidget(btn_monitor)
        layout.addWidget(btn_logout)
        layout.addSpacing(6)
        layout.addWidget(self.theme_btn)

    def set_user(self, username):
        self.avatar.set_username(username)
        self.username_label.setText(username)

    def set_theme_icon(self, theme_name: str):
        self.theme_btn.setText("☀️" if theme_name == "dark" else "🌙")

    def apply_theme(self, theme_name: str):
        t = APP_THEMES[theme_name]
        self.setStyleSheet(f"background-color: {t['bg_surface']}; border-bottom: 1px solid {t['border']};")


# ---------------- DASHBOARD SHELL ----------------

class DashboardShell(QWidget):

    logout_requested = Signal()
    theme_toggle_requested = Signal()

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = Header()

        self.pages = QStackedWidget()

        self.home_page = HomePage()
        self.monitor_page = MonitorPage()

        self.pages.addWidget(self.home_page)
        self.pages.addWidget(self.monitor_page)

        layout.addWidget(self.header)
        layout.addWidget(self.pages)

        self.header.page_requested.connect(self.change_page)
        self.header.logout_requested.connect(self.logout_requested.emit)
        self.header.theme_toggle_requested.connect(self.theme_toggle_requested.emit)

    def set_user(self, user_data):
        username = user_data["username"]
        self.header.set_user(username)

        if hasattr(self.home_page, "set_user_info"):
            self.home_page.set_user_info(user_data)

    def change_page(self, page):
        if page == "home":
            self.pages.setCurrentWidget(self.home_page)
        elif page == "monitor":
            self.pages.setCurrentWidget(self.monitor_page)

    def apply_theme(self, theme_name: str):
        self.header.apply_theme(theme_name)
        self.header.set_theme_icon(theme_name)
        self.home_page.apply_theme(theme_name)
        self.monitor_page.apply_theme(theme_name)


# ---------------- MAIN APP ----------------

class MainApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DAPS")

        self.theme_name = "dark"
        self._logged_in = False

        # Login screen fixed size
        self.setFixedSize(500, 350)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = LoginPage()
        self.stack.addWidget(self.login_page)
        self.stack.setCurrentWidget(self.login_page)

        # DashboardShell (HomePage + MonitorPage + alerts panel + CPU chart)
        # is NOT built here. Building it eagerly meant paying that whole
        # construction cost before the login screen could even appear.
        # It's built once, lazily, the first time login actually succeeds.
        self.dashboard = None

        self.login_page.login_success.connect(self.login_complete)

        # ---------------- FLOATING THEME TOGGLE ----------------
        # Lives directly on MainApp (not inside Header) so it's available
        # on the login screen. Hidden after login in favor of the one
        # docked in Header (see login_complete).
        self.theme_btn = QPushButton("🌙", self)
        self.theme_btn.setFixedSize(28, 28)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("Toggle dark / light theme")
        self.theme_btn.clicked.connect(self.toggle_theme)
        self._style_theme_button()
        self._position_theme_button()
        self.theme_btn.raise_()

        self.apply_theme(self.theme_name)

        # Background threads start shortly AFTER the window is on screen,
        # not before — so WMI/watchdog startup work doesn't compete with
        # (and delay) the login screen's very first paint.
        QTimer.singleShot(150, self._start_background_threads)

    def _start_background_threads(self):
        # ---------------- USB MONITOR (background) ----------------
        # Runs silently: no UI, all activity logged to logs.db via db_logger.
        self._usb_stop_event = threading.Event()
        self._usb_thread = threading.Thread(
            target=run_usb_monitor,
            args=(self._usb_stop_event,),
            daemon=True
        )
        self._usb_thread.start()

        # ---------------- FILE WATCHDOG (background) ----------------
        # Watches Company DB for changes made outside the app.
        self._watchdog_stop_event = threading.Event()
        self._watchdog_thread = threading.Thread(
            target=run_file_watchdog,
            args=(self._watchdog_stop_event,),
            daemon=True
        )
        self._watchdog_thread.start()

    def _style_theme_button(self):
        # Deliberately plain/borderless — overrides the global QPushButton
        # pill-button style so this reads as an icon toggle, not a big blue box.
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 18px;
                font-size: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 35);
            }
        """)

    def _position_theme_button(self):
        # Only relevant pre-login now — post-login uses Header's own
        # theme button instead, laid out properly next to Logout.
        top_y = 4
        right_margin = 150  # clears the native minimize/maximize/close buttons
        self.theme_btn.move(
            self.width() - self.theme_btn.width() - right_margin,
            top_y
        )
        self.theme_btn.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_theme_button()

    def closeEvent(self, event):
        if self._logged_in:
            # Block the OS close button / Alt+F4 while a session is active.
            # The user must use the Logout button instead.
            event.ignore()
            QMessageBox.information(
                self,
                "Logout Required",
                "Please use the Logout button to close a session."
            )
            return

        if hasattr(self, "_usb_stop_event"):
            self._usb_stop_event.set()
        if hasattr(self, "_watchdog_stop_event"):
            self._watchdog_stop_event.set()
        event.accept()

    def apply_theme(self, theme_name: str):
        self.theme_name = theme_name

        app = QApplication.instance()
        app.setStyleSheet(build_global_stylesheet(theme_name))

        if self.dashboard is not None:
            self.dashboard.apply_theme(theme_name)

        self.theme_btn.setText("☀️" if theme_name == "dark" else "🌙")
        self._position_theme_button()

    def toggle_theme(self):
        new_theme = "light" if self.theme_name == "dark" else "dark"
        self.apply_theme(new_theme)

    def handle_logout(self):

        if hasattr(self.login_page, "username_input"):
            self.login_page.username_input.clear()
        if hasattr(self.login_page, "password_input"):
            self.login_page.password_input.clear()

        self._logged_in = False

        self.stack.setCurrentWidget(self.login_page)

        self.setMinimumSize(0, 0)
        self.setFixedSize(500, 350)

        # restore normal window chrome (minimize/close available on login screen)
        self.setWindowFlags(Qt.Window)
        self.show()
        self.theme_btn.setVisible(True)
        self._position_theme_button()

    def login_complete(self, user_data):

        if self.dashboard is None:
            # First login: build the dashboard now, not at app startup.
            self.dashboard = DashboardShell()
            self.stack.addWidget(self.dashboard)
            self.dashboard.logout_requested.connect(self.handle_logout)
            self.dashboard.theme_toggle_requested.connect(self.toggle_theme)
            self.dashboard.apply_theme(self.theme_name)

        self.dashboard.set_user(user_data)

        self.stack.setCurrentWidget(self.dashboard)

        self._logged_in = True

        # strip minimize/maximize/close buttons — logout is the only way out
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)

        # unlock resizing after login
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.showMaximized()

        # Header now has its own theme button, properly laid out next to
        # Logout — hide the floating one so there's only ever one visible.
        self.theme_btn.setVisible(False)


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = MainApp()
    window.show()

    sys.exit(app.exec())