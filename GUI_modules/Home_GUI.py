from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QPushButton,
    QGraphicsOpacityEffect, QMessageBox, QScrollArea,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Property, QTimer
from PySide6.QtGui import QColor
import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from Filecrypter.encryption.encrypt import encrypt_file
from Filecrypter.encryption.decrypt import decrypt_file

alerts_dir = root_dir / "alerts"
if str(alerts_dir) not in sys.path:
    sys.path.insert(0, str(alerts_dir))

from Maneater.alerts.alert_manager import get_recent_alerts, acknowledge_all_alerts


# ── palette ──
BG_DEEP    = "#0D1B2A"
BG_SURFACE = "#1C2E42"
ACCENT     = "#4A9EBF"
ACCENT_DARK= "#2E7A9A"
TEXT_PRI   = "#F0F4F8"
TEXT_SEC   = "#8FA8BF"
BORDER     = "#2A4059"
SUCCESS    = "#3CB371"
SUCCESS_DK = "#2A8A58"


# ─────────────────────────────────────────
#  ALERTS PANEL (manager-only)
# ─────────────────────────────────────────
SEVERITY_COLORS = {
    "CRITICAL": "#E25858",
    "WARNING":  "#E2A83D",
    "INFO":     ACCENT,
}


class AlertRow(QFrame):

    def __init__(self, source, severity, title, message, timestamp):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        color = SEVERITY_COLORS.get(severity, TEXT_SEC)

        top_line = QLabel(f"[{severity}]  {source} — {title}")
        top_line.setStyleSheet(f"""
            color: {color}; font-size: 13px; font-weight: 700;
            background: transparent; border: none;
        """)

        message_line = QLabel(message)
        message_line.setStyleSheet(f"""
            color: {TEXT_PRI}; font-size: 12px;
            background: transparent; border: none;
        """)
        message_line.setWordWrap(True)

        time_line = QLabel(timestamp)
        time_line.setStyleSheet(f"""
            color: {TEXT_SEC}; font-size: 10px;
            background: transparent; border: none;
        """)

        layout.addWidget(top_line)
        layout.addWidget(message_line)
        layout.addWidget(time_line)


class AlertsPanel(QWidget):

    def __init__(self):
        super().__init__()
        self.setVisible(False)  # shown only for managers, via set_manager_mode()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        header_row = QHBoxLayout()

        header_label = QLabel("PENDING ALERTS")
        header_label.setStyleSheet(f"""
            color: {TEXT_SEC}; font-size: 10px; font-weight: 600;
            letter-spacing: 2px; background: transparent; border: none;
        """)
        header_row.addWidget(header_label)
        header_row.addStretch()

        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.setFixedHeight(28)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {ACCENT};
                border: 1px solid {ACCENT};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0px 12px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT};
                color: {TEXT_PRI};
            }}
        """)
        self._clear_btn.clicked.connect(self._clear_all)
        header_row.addWidget(self._clear_btn)

        outer.addLayout(header_row)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setMaximumHeight(220)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        self._scroll.setWidget(self._list_widget)
        outer.addWidget(self._scroll)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(3000)  # poll every 3 seconds

    def refresh(self):
        if not self.isVisible():
            return

        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # rows: (id, source, severity, title, message, timestamp, acknowledged)
        alerts = get_recent_alerts(limit=100, acknowledged=False)

        if not alerts:
            empty = QLabel("No pending alerts")
            empty.setStyleSheet(f"color: {TEXT_SEC}; font-size: 12px; background: transparent; border: none;")
            self._list_layout.addWidget(empty)
        else:
            for row in alerts:
                _id, source, severity, title, message, timestamp, _ack = row
                self._list_layout.addWidget(
                    AlertRow(source, severity, title, message, timestamp)
                )

        self._list_layout.addStretch()

    def _clear_all(self):
        acknowledge_all_alerts()
        self.refresh()

    def set_manager_mode(self, is_manager: bool):
        self.setVisible(is_manager)
        if is_manager:
            self.refresh()


# ─────────────────────────────────────────
#  COLLAPSIBLE INFO PANEL
# ─────────────────────────────────────────
class CollapsiblePanel(QWidget):
    """Animated slide-down panel for user details."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = False
        self.setMaximumHeight(0)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 16)
        layout.setSpacing(16)

        self._email_card, self._email_val = self._make_card("Email", "—")
        self._role_card,  self._role_val  = self._make_card("Role",  "—")
        self._dept_card,  self._dept_val  = self._make_card("Department", "—")

        layout.addWidget(self._email_card)
        layout.addWidget(self._role_card)
        layout.addWidget(self._dept_card)

        # measure collapsed vs expanded height
        self._full_height = 90

        self._anim = QPropertyAnimation(self, b"maximumHeight")
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

    def _make_card(self, label: str, value: str):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
        """)
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setFixedHeight(72)

        fl = QVBoxLayout(frame)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(4)

        lbl = QLabel(label.upper())
        lbl.setStyleSheet(f"""
            color: {TEXT_SEC}; font-size: 10px; font-weight: 600;
            letter-spacing: 1px; background: transparent; border: none;
        """)

        val = QLabel(value)
        val.setStyleSheet(f"""
            color: {TEXT_PRI}; font-size: 14px; font-weight: 600;
            background: transparent; border: none;
        """)
        val.setWordWrap(True)

        fl.addWidget(lbl)
        fl.addWidget(val)
        return frame, val

    def set_user(self, user_data: dict):
        self._email_val.setText(user_data.get("email", "—"))
        self._role_val.setText(user_data.get("role", "—"))
        self._dept_val.setText(user_data.get("department") or "None")

    def toggle(self):
        if self._expanded:
            self._anim.setStartValue(self._full_height)
            self._anim.setEndValue(0)
        else:
            self._anim.setStartValue(0)
            self._anim.setEndValue(self._full_height)
        self._expanded = not self._expanded
        self._anim.start()

    @property
    def expanded(self):
        return self._expanded


# ─────────────────────────────────────────
#  HOME PAGE
# ─────────────────────────────────────────
class HomePage(QWidget):

    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"background-color: {BG_DEEP};")
        self._user_data = {}
        self.username = ""
        root = QVBoxLayout(self)
        root.setContentsMargins(48, 40, 48, 48)
        root.setSpacing(0)

        # ── greeting row ──
        greeting_row = QHBoxLayout()
        greeting_row.setSpacing(10)
        greeting_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self._greeting = QLabel("Welcome back.")
        self._greeting.setStyleSheet(f"""
            color: {TEXT_PRI};
            font-size: 26px;
            font-weight: 700;
            font-family: 'Segoe UI', sans-serif;
        """)

        # chevron toggle button (▾ / ▴)
        self._toggle_btn = QPushButton("▾")
        self._toggle_btn.setFixedSize(28, 28)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT_SEC};
                font-size: 14px;
                padding: 0px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {ACCENT};
                background: transparent;
            }}
        """)
        self._toggle_btn.clicked.connect(self._toggle_details)

        greeting_row.addWidget(self._greeting)
        greeting_row.addWidget(self._toggle_btn, alignment=Qt.AlignVCenter)
        greeting_row.addStretch()

        root.addLayout(greeting_row)
        root.addSpacing(4)

        self._sub = QLabel("Click ▾ to view your account details.")
        self._sub.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 13px;
            font-family: 'Segoe UI', sans-serif;
        """)
        root.addWidget(self._sub)

        # ── collapsible details panel ──
        self._panel = CollapsiblePanel()
        root.addWidget(self._panel)

        # ── alerts panel (managers only) ──
        self._alerts_panel = AlertsPanel()
        root.addWidget(self._alerts_panel)
        root.addSpacing(16)

        # ── divider ──
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {BORDER}; border: none;")
        root.addSpacing(8)
        root.addWidget(div)
        root.addSpacing(28)

        # ── action cards row ──
        actions_label = QLabel("ACTIONS")
        actions_label.setStyleSheet(f"""
            color: {TEXT_SEC};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 2px;
        """)
        root.addWidget(actions_label)
        root.addSpacing(12)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)

        # Upload card
        upload_card = self._make_action_card(
            title="Upload & Encrypt",
            description="Select a file to encrypt and protect it with AES.",
            button_text="Upload File",
            button_color=ACCENT,
            button_hover=ACCENT_DARK,
            slot=self._on_upload,
        )

        # Fetch card
        fetch_card = self._make_action_card(
            title="Fetch & Decrypt",
            description="Select an encrypted .daps file to decrypt and open.",
            button_text="Fetch File",
            button_color=SUCCESS,
            button_hover=SUCCESS_DK,
            slot=self._on_fetch,
        )

        cards_row.addWidget(upload_card)
        cards_row.addWidget(fetch_card)
        cards_row.addStretch()

        root.addLayout(cards_row)
        root.addStretch()

    # ── helpers ──

    def _make_action_card(self, title, description, button_text,
                          button_color, button_hover, slot):
        card = QFrame()
        card.setFixedWidth(260)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
        """)

        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(8)

        t = QLabel(title)
        t.setStyleSheet(f"""
            color: {TEXT_PRI}; font-size: 15px; font-weight: 700;
            background: transparent; border: none;
        """)

        d = QLabel(description)
        d.setStyleSheet(f"""
            color: {TEXT_SEC}; font-size: 12px;
            background: transparent; border: none;
        """)
        d.setWordWrap(True)

        btn = QPushButton(button_text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(36)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {button_color};
                color: {TEXT_PRI};
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QPushButton:pressed {{
                background-color: {button_hover};
            }}
        """)
        btn.clicked.connect(slot)

        cl.addWidget(t)
        cl.addWidget(d)
        cl.addSpacing(6)
        cl.addWidget(btn)
        return card

    def _toggle_details(self):
        self._panel.toggle()
        if self._panel.expanded:
            self._toggle_btn.setText("▴")
            self._sub.setText("Your account details.")
        else:
            self._toggle_btn.setText("▾")
            self._sub.setText("Click ▾ to view your account details.")

    def _on_upload(self):

        if not self.username:
            return

        try:

            encrypted_file = encrypt_file(self.username)

            if encrypted_file:

                print("Encrypted Successfully")

                QMessageBox.information(

                    self,

                    "Success",

                    f"Encrypted File Stored Successfully\n\n{encrypted_file}"

                )

        except Exception as e:

            print("Upload Error")

            QMessageBox.critical(

                self,

                "Error",

                str(e)

            )

    def _on_fetch(self):

        if not self.username:
            return

        try:

            decrypted_file = decrypt_file(self.username)

            if decrypted_file:

                print("Decrypted Successfully")

                QMessageBox.information(

                    self,

                    "Success",

                    f"Recovered File\n\n{decrypted_file}"

                )

        except Exception as e:

            print("Fetch Error")

            QMessageBox.critical(

                self,

                "Error",

                str(e)

            )

    def set_user_info(self, user_data: dict):
        self._user_data = user_data
        self.username = user_data.get("username", "User")
        self._greeting.setText(f"Welcome back, {self.username}.")
        self._panel.set_user(user_data)

        role = str(user_data.get("role", "")).strip().lower()
        self._alerts_panel.set_manager_mode(role == "manager")