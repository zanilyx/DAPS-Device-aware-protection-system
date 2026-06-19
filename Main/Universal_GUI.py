from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QFrame,
    QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import (
    QPainter,
    QColor,
    QFont,
    QLinearGradient,
    QPen,
    QCursor,
)
from PySide6.QtCore import Qt, QRect
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from GUI_modules.Login_page_GUI import LoginPage
from GUI_modules.Home_GUI import HomePage


# ─────────────────────────────────────────
#  COLOUR PALETTE  (single source of truth)
# ─────────────────────────────────────────
BG_DEEP     = "#0D1B2A"   # window / page background
BG_SURFACE  = "#1C2E42"   # header / card background
ACCENT      = "#4A9EBF"   # ice-blue primary accent
ACCENT_DARK = "#2E7A9A"   # darker accent (hover)
TEXT_PRI    = "#F0F4F8"   # primary text
TEXT_SEC    = "#8FA8BF"   # secondary / muted text
BORDER      = "#2A4059"   # subtle border colour


# ─────────────────────────────────────────
#  AVATAR
# ─────────────────────────────────────────
class Avatar(QWidget):
    """Circular avatar with initials and a glowing accent ring."""

    def __init__(self, username: str = "?", size: int = 38):
        super().__init__()
        self.username = username
        self.avatar_size = size
        self.setFixedSize(size, size)

    def set_username(self, username: str):
        self.username = username
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        margin = 2

        # ── glow ring ──
        pen = QPen(QColor(ACCENT))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(margin, margin, w - margin * 2, h - margin * 2)

        # ── filled circle ──
        inner = margin + 3
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(BG_SURFACE))
        painter.drawEllipse(inner, inner, w - inner * 2, h - inner * 2)

        # ── initial letter ──
        painter.setPen(QColor(ACCENT))
        font = QFont("Segoe UI", int(self.avatar_size * 0.38), QFont.Bold)
        painter.setFont(font)
        letter = (self.username[0].upper() if self.username else "?")
        painter.drawText(self.rect(), Qt.AlignCenter, letter)


# ─────────────────────────────────────────
#  PROFILE POPUP
# ─────────────────────────────────────────
class ProfilePopup(QFrame):
    """Floating card shown below the avatar on click."""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        # NOTE: WA_TranslucentBackground + QGraphicsDropShadowEffect causes
        # UpdateLayeredWindowIndirect errors on Windows when near screen edges.
        # Use a solid background with a visible border instead.
        self.setFixedWidth(220)

        self.setStyleSheet(f"""
            ProfilePopup {{
                background-color: {BG_SURFACE};
                border: 1px solid {ACCENT};
                border-radius: 0px;
            }}
            QLabel#name {{
                color: {TEXT_PRI};
                font-size: 15px;
                font-weight: 700;
            }}
            QLabel#meta {{
                color: {TEXT_SEC};
                font-size: 12px;
            }}
            QLabel#divider {{
                background-color: {BORDER};
                min-height: 1px;
                max-height: 1px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 14)
        layout.setSpacing(6)

        # Large avatar inside popup
        avatar_row = QHBoxLayout()
        avatar_row.setAlignment(Qt.AlignCenter)
        self.big_avatar = Avatar(username="?", size=56)
        avatar_row.addWidget(self.big_avatar)
        layout.addLayout(avatar_row)

        layout.addSpacing(6)

        self.name_label = QLabel("Guest")
        self.name_label.setObjectName("name")
        self.name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_label)

        self.role_label = QLabel("")
        self.role_label.setObjectName("meta")
        self.role_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.role_label)

        self.email_label = QLabel("")
        self.email_label.setObjectName("meta")
        self.email_label.setAlignment(Qt.AlignCenter)
        self.email_label.setWordWrap(True)
        layout.addWidget(self.email_label)

        div = QLabel()
        div.setObjectName("divider")
        layout.addSpacing(8)
        layout.addWidget(div)

    def set_user(self, user_data: dict):
        username = user_data.get("username", "Guest")
        self.big_avatar.set_username(username)
        self.name_label.setText(username)
        self.role_label.setText(user_data.get("role", ""))
        self.email_label.setText(user_data.get("email", ""))

    def show_below(self, widget: QWidget):
        """Position popup below the given widget and show."""
        pos = widget.mapToGlobal(QPoint(0, widget.height() + 6))
        # Centre the popup horizontally under the avatar
        pos.setX(pos.x() - self.width() // 2 + widget.width() // 2)
        self.move(pos)
        self.show()


# ─────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────
class Header(QWidget):
    """Slim dark top-bar: clickable avatar left, DAPS title centred."""

    page_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(56)
        self._user_data = {}

        self.setStyleSheet(f"""
            Header {{
                background-color: {BG_SURFACE};
                border-bottom: 1px solid {BORDER};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(0)

        # ── left: avatar (clickable) ──
        self.avatar = Avatar(username="?", size=34)
        self.avatar.setCursor(QCursor(Qt.PointingHandCursor))
        self.avatar.mousePressEvent = self._on_avatar_clicked
        layout.addWidget(self.avatar, alignment=Qt.AlignVCenter)

        # ── centre: app name ──
        layout.addStretch()
        app_label = QLabel("DAPS")
        app_label.setStyleSheet(f"""
            color: {TEXT_PRI};
            font-family: 'Segoe UI', sans-serif;
            font-size: 17px;
            font-weight: 700;
            letter-spacing: 3px;
        """)
        layout.addWidget(app_label, alignment=Qt.AlignVCenter)
        layout.addStretch()

        # ── right: symmetric filler ──
        filler = QWidget()
        filler.setFixedWidth(self.avatar.width())
        filler.setStyleSheet("background: transparent;")
        layout.addWidget(filler)

        # Popup (no parent → floats as a top-level window)
        self._popup = ProfilePopup()

    def set_user(self, username: str, user_data: dict = None):
        self._user_data = user_data or {"username": username}
        self.avatar.set_username(username)

    def _on_avatar_clicked(self, event):
        if self._popup.isVisible():
            self._popup.hide()
        else:
            self._popup.set_user(self._user_data)
            self._popup.show_below(self.avatar)


# ─────────────────────────────────────────
#  DASHBOARD SHELL
# ─────────────────────────────────────────
class DashboardShell(QWidget):

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG_DEEP};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.header = Header()

        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background: transparent;")

        self.home_page = HomePage()
        self.pages.addWidget(self.home_page)

        layout.addWidget(self.header)
        layout.addWidget(self.pages)

        self.header.page_requested.connect(self.change_page)

    def set_user(self, user_data: dict):
        username = user_data.get("username", "User")
        self.header.set_user(username, user_data)
        if hasattr(self.home_page, "set_user_info"):
            self.home_page.set_user_info(user_data)

    def change_page(self, page: str):
        if page == "home":
            self.pages.setCurrentWidget(self.home_page)


# ─────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────
class MainApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAPS")
        self.setFixedSize(500, 350)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {BG_DEEP};
            }}
            QWidget {{
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }}
            QLabel {{
                color: {TEXT_PRI};
            }}
            QPushButton {{
                background-color: {ACCENT};
                color: {TEXT_PRI};
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_DARK};
            }}
            QPushButton:pressed {{
                background-color: #1F5F7A;
            }}
        """)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.login_page = LoginPage()
        self.dashboard  = DashboardShell()

        self.stack.addWidget(self.login_page)
        self.stack.addWidget(self.dashboard)
        self.stack.setCurrentWidget(self.login_page)

        self.login_page.login_success.connect(self.login_complete)

    def login_complete(self, user_data: dict):
        self.dashboard.set_user(user_data)
        self.stack.setCurrentWidget(self.dashboard)

        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        self.showMaximized()


# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())