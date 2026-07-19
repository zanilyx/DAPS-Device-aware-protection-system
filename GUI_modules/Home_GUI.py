from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QSizePolicy, QPushButton,
    QGraphicsOpacityEffect, QMessageBox, QScrollArea,
    QGraphicsDropShadowEffect, QFileDialog,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Property, QTimer, QThread, Signal
from PySide6.QtGui import QColor
import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from Filecrypter.encryption.encrypt import encrypt_file_core, get_user_details
from Filecrypter.encryption.decrypt import decrypt_file_core
from GUI_modules.role_dialog import RoleSelectionDialog

alerts_dir = root_dir / "Maneater" / "alerts"
if str(alerts_dir) not in sys.path:
    sys.path.insert(0, str(alerts_dir))

from alert_manager import get_recent_alerts, acknowledge_all_alerts


# ─────────────────────────────────────────
#  THEMES
# ─────────────────────────────────────────
THEMES = {
    "dark": dict(
        BG_DEEP="#0D1B2A",
        BG_SURFACE="#1C2E42",
        ACCENT="#4A9EBF",
        ACCENT_DARK="#2E7A9A",
        TEXT_PRI="#F0F4F8",
        TEXT_SEC="#8FA8BF",
        BORDER="#2A4059",
        SUCCESS="#3CB371",
        SUCCESS_DK="#2A8A58",
    ),
    "light": dict(
        BG_DEEP="#EEF2F6",
        BG_SURFACE="#FFFFFF",
        ACCENT="#2E7A9A",
        ACCENT_DARK="#1F5C77",
        TEXT_PRI="#16232F",
        TEXT_SEC="#51697E",
        BORDER="#D7E0E8",
        SUCCESS="#2A8A58",
        SUCCESS_DK="#1F6B43",
    ),
}

SEVERITY_COLORS = {
    "CRITICAL": "#E25858",
    "WARNING":  "#E2A83D",
    "INFO":     None,  # resolved to ACCENT at render time
}


def _shadow(blur=24, color="#000000", alpha=90, y_offset=6):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(blur)
    c = QColor(color)
    c.setAlpha(alpha)
    effect.setColor(c)
    effect.setOffset(0, y_offset)
    return effect


# ─────────────────────────────────────────
#  ALERTS PANEL (manager-only)
# ─────────────────────────────────────────
class AlertRow(QFrame):

    def __init__(self, source, severity, title, message, timestamp, theme):
        super().__init__()
        self._build(source, severity, title, message, timestamp, theme)

    def _build(self, source, severity, title, message, timestamp, theme):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['BG_SURFACE']};
                border: 1px solid {theme['BORDER']};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        color = SEVERITY_COLORS.get(severity) or theme["ACCENT"]

        top_line = QLabel(f"[{severity}]  {source} — {title}")
        top_line.setStyleSheet(f"""
            color: {color}; font-size: 13px; font-weight: 700;
            background: transparent; border: none;
        """)

        message_line = QLabel(message)
        message_line.setStyleSheet(f"""
            color: {theme['TEXT_PRI']}; font-size: 12px;
            background: transparent; border: none;
        """)
        message_line.setWordWrap(True)

        time_line = QLabel(timestamp)
        time_line.setStyleSheet(f"""
            color: {theme['TEXT_SEC']}; font-size: 10px;
            background: transparent; border: none;
        """)

        layout.addWidget(top_line)
        layout.addWidget(message_line)
        layout.addWidget(time_line)


class AlertsPanel(QWidget):

    def __init__(self, theme):
        super().__init__()
        self.theme = theme
        self.setVisible(False)  # shown only for managers, via set_manager_mode()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        header_row = QHBoxLayout()

        self._header_label = QLabel("PENDING ALERTS")
        header_row.addWidget(self._header_label)
        header_row.addStretch()

        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.setFixedHeight(28)
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

        self.apply_theme(theme)

    def apply_theme(self, theme):
        self.theme = theme

        self._header_label.setStyleSheet(f"""
            color: {theme['TEXT_SEC']}; font-size: 10px; font-weight: 600;
            letter-spacing: 2px; background: transparent; border: none;
        """)

        hover_text = "#0D1B2A" if theme["BG_SURFACE"] == "#FFFFFF" else theme["TEXT_PRI"]

        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {theme['ACCENT']};
                border: 1px solid {theme['ACCENT']};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0px 12px;
            }}
            QPushButton:hover {{
                background-color: {theme['ACCENT']};
                color: {hover_text};
            }}
        """)

        self.refresh()

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
            empty.setStyleSheet(f"color: {self.theme['TEXT_SEC']}; font-size: 12px; background: transparent; border: none;")
            self._list_layout.addWidget(empty)
        else:
            for row in alerts:
                _id, source, severity, title, message, timestamp, _ack = row
                self._list_layout.addWidget(
                    AlertRow(source, severity, title, message, timestamp, self.theme)
                )

        self._list_layout.addStretch()

    def _clear_all(self):
        acknowledge_all_alerts()
        self.refresh()

    def set_manager_mode(self, is_manager: bool):
        self.setVisible(is_manager)
        if is_manager:
            self.refresh()


class _CryptoWorker(QThread):
    """
    Runs a (success, message, output_path) function on a background
    thread so large-file encryption/decryption doesn't freeze the GUI.
    Only call thread-safe "core" functions here — never QFileDialog,
    RoleSelectionDialog, or QMessageBox from inside fn.
    """

    finished_result = Signal(bool, str, object)

    def __init__(self, fn, args):
        super().__init__()
        self.fn = fn
        self.args = args

    def run(self):
        success, message, output_path = self.fn(*self.args)
        self.finished_result.emit(success, message, output_path)


# ─────────────────────────────────────────
#  COLLAPSIBLE INFO PANEL
# ─────────────────────────────────────────
class CollapsiblePanel(QWidget):
    """Animated slide-down panel for user details."""

    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self._expanded = False
        self.setMaximumHeight(0)
        self.setStyleSheet("background: transparent;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 8, 0, 16)
        self._layout.setSpacing(16)

        self._email_card, self._email_val, self._email_lbl = self._make_card("Email", "—")
        self._role_card,  self._role_val,  self._role_lbl  = self._make_card("Role",  "—")
        self._dept_card,  self._dept_val,  self._dept_lbl  = self._make_card("Department", "—")

        self._layout.addWidget(self._email_card)
        self._layout.addWidget(self._role_card)
        self._layout.addWidget(self._dept_card)

        self._full_height = 90

        self._anim = QPropertyAnimation(self, b"maximumHeight")
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.apply_theme(theme)

    def _make_card(self, label: str, value: str):
        frame = QFrame()
        frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        frame.setFixedHeight(72)

        fl = QVBoxLayout(frame)
        fl.setContentsMargins(16, 10, 16, 10)
        fl.setSpacing(4)

        lbl = QLabel(label.upper())
        val = QLabel(value)
        val.setWordWrap(True)

        fl.addWidget(lbl)
        fl.addWidget(val)
        return frame, val, lbl

    def apply_theme(self, theme):
        self.theme = theme

        frame_style = f"""
            QFrame {{
                background-color: {theme['BG_SURFACE']};
                border: 1px solid {theme['BORDER']};
                border-radius: 8px;
            }}
        """
        label_style = f"""
            color: {theme['TEXT_SEC']}; font-size: 10px; font-weight: 600;
            letter-spacing: 1px; background: transparent; border: none;
        """
        value_style = f"""
            color: {theme['TEXT_PRI']}; font-size: 14px; font-weight: 600;
            background: transparent; border: none;
        """

        for card, val, lbl in (
            (self._email_card, self._email_val, self._email_lbl),
            (self._role_card, self._role_val, self._role_lbl),
            (self._dept_card, self._dept_val, self._dept_lbl),
        ):
            card.setStyleSheet(frame_style)
            val.setStyleSheet(value_style)
            lbl.setStyleSheet(label_style)

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
        self.theme_name = "dark"
        self.theme = THEMES[self.theme_name]

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

        self._toggle_btn = QPushButton("▾")
        self._toggle_btn.setFixedSize(28, 28)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.clicked.connect(self._toggle_details)

        greeting_row.addWidget(self._greeting)
        greeting_row.addWidget(self._toggle_btn, alignment=Qt.AlignVCenter)
        greeting_row.addStretch()

        root.addLayout(greeting_row)
        root.addSpacing(4)

        self._sub = QLabel("Click ▾ to view your account details.")
        root.addWidget(self._sub)

        # ── collapsible details panel ──
        self._panel = CollapsiblePanel(self.theme)
        root.addWidget(self._panel)

        # ── alerts panel (managers only) ──
        self._alerts_panel = AlertsPanel(self.theme)
        root.addWidget(self._alerts_panel)
        root.addSpacing(16)

        # ── divider ──
        self._div = QFrame()
        self._div.setFixedHeight(1)
        root.addSpacing(8)
        root.addWidget(self._div)
        root.addSpacing(28)

        # ── action cards row ──
        self._actions_label = QLabel("ACTIONS")
        root.addWidget(self._actions_label)
        root.addSpacing(12)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(20)

        self._upload_widgets = self._make_action_card(
            title="Upload & Encrypt",
            description="Select a file to encrypt and protect it with AES.",
            button_text="Upload File",
            slot=self._on_upload,
            accent_key="ACCENT",
        )

        self._fetch_widgets = self._make_action_card(
            title="Fetch & Decrypt",
            description="Select an encrypted .daps file to decrypt and open.",
            button_text="Fetch File",
            slot=self._on_fetch,
            accent_key="SUCCESS",
        )

        cards_row.addWidget(self._upload_widgets["card"])
        cards_row.addWidget(self._fetch_widgets["card"])
        cards_row.addStretch()

        root.addLayout(cards_row)
        root.addStretch()

        self.apply_theme("dark")

    # ── helpers ──

    def _make_action_card(self, title, description, button_text, slot, accent_key):
        card = QFrame()
        card.setFixedWidth(260)
        card.setGraphicsEffect(_shadow())

        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 20, 20, 20)
        cl.setSpacing(8)

        t = QLabel(title)
        d = QLabel(description)
        d.setWordWrap(True)

        btn = QPushButton(button_text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(36)
        btn.clicked.connect(slot)

        cl.addWidget(t)
        cl.addWidget(d)
        cl.addSpacing(6)
        cl.addWidget(btn)

        return {
            "card": card, "title": t, "desc": d, "btn": btn,
            "accent_key": accent_key,
        }

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

        # File picking and the role dialog stay on the GUI thread — only
        # the heavy key-gen/encryption/file-IO work below moves off it.
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select File to Encrypt",
            ""
        )
        if not file_path:
            return

        department, user_role = get_user_details(self.username)
        if department is None:
            QMessageBox.warning(self, "Error", "User not found.")
            return

        dialog = RoleSelectionDialog(user_role)
        if not dialog.exec():
            return

        classification, allowed_roles = dialog.get_data()

        btn = self._upload_widgets["btn"]
        btn.setEnabled(False)
        btn.setText("Encrypting…")

        self._encrypt_thread = _CryptoWorker(
            encrypt_file_core,
            (self.username, file_path, classification, allowed_roles)
        )
        self._encrypt_thread.finished_result.connect(self._on_encrypt_finished)
        self._encrypt_thread.start()

    def _on_encrypt_finished(self, success, message, output_path):
        btn = self._upload_widgets["btn"]
        btn.setEnabled(True)
        btn.setText("Upload File")

        if success:
            print("Encrypted Successfully")
            QMessageBox.information(self, "Encryption Successful", message)
        else:
            print("Upload Error:", message)
            QMessageBox.critical(self, "Encryption Failed", message)

    def _on_fetch(self):

        if not self.username:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Encrypted File",
            "",
            "DAPS Files (*.daps)"
        )
        if not file_path:
            return

        btn = self._fetch_widgets["btn"]
        btn.setEnabled(False)
        btn.setText("Decrypting…")

        self._decrypt_thread = _CryptoWorker(
            decrypt_file_core,
            (self.username, file_path)
        )
        self._decrypt_thread.finished_result.connect(self._on_decrypt_finished)
        self._decrypt_thread.start()

    def _on_decrypt_finished(self, success, message, output_path):
        btn = self._fetch_widgets["btn"]
        btn.setEnabled(True)
        btn.setText("Fetch File")

        if success:
            print("Decrypted Successfully")
            QMessageBox.information(self, "Success", message)
        else:
            print("Fetch Error:", message)
            QMessageBox.warning(self, "Decryption Failed", message)

    def set_user_info(self, user_data: dict):
        self._user_data = user_data
        self.username = user_data.get("username", "User")
        self._greeting.setText(f"Welcome back, {self.username}.")
        self._panel.set_user(user_data)

        role = str(user_data.get("role", "")).strip().lower()
        self._alerts_panel.set_manager_mode(role == "manager")

    # ── theming ──

    def apply_theme(self, theme_name: str):
        self.theme_name = theme_name
        theme = THEMES[theme_name]
        self.theme = theme

        self.setStyleSheet(f"background-color: {theme['BG_DEEP']};")

        self._greeting.setStyleSheet(f"""
            color: {theme['TEXT_PRI']};
            font-size: 27px;
            font-weight: 700;
            font-family: 'Segoe UI', sans-serif;
        """)

        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {theme['BORDER']};
                border-radius: 6px;
                color: {theme['TEXT_SEC']};
                font-size: 14px;
                padding: 0px;
            }}
            QPushButton:hover {{
                border-color: {theme['ACCENT']};
                color: {theme['ACCENT']};
                background: transparent;
            }}
        """)

        self._sub.setStyleSheet(f"""
            color: {theme['TEXT_SEC']};
            font-size: 13px;
            font-family: 'Segoe UI', sans-serif;
        """)

        self._div.setStyleSheet(f"background-color: {theme['BORDER']}; border: none;")

        self._actions_label.setStyleSheet(f"""
            color: {theme['TEXT_SEC']};
            font-size: 10px;
            font-weight: 600;
            letter-spacing: 2px;
        """)

        self._panel.apply_theme(theme)
        self._alerts_panel.apply_theme(theme)

        for widgets in (self._upload_widgets, self._fetch_widgets):
            accent = theme[widgets["accent_key"]]
            accent_dark_key = "ACCENT_DARK" if widgets["accent_key"] == "ACCENT" else "SUCCESS_DK"
            accent_hover = theme[accent_dark_key]
            btn_text_color = "#0D1B2A" if theme_name == "light" else theme["TEXT_PRI"]

            widgets["card"].setStyleSheet(f"""
                QFrame {{
                    background-color: {theme['BG_SURFACE']};
                    border: 1px solid {theme['BORDER']};
                    border-radius: 12px;
                }}
            """)
            widgets["title"].setStyleSheet(f"""
                color: {theme['TEXT_PRI']}; font-size: 15px; font-weight: 700;
                background: transparent; border: none;
            """)
            widgets["desc"].setStyleSheet(f"""
                color: {theme['TEXT_SEC']}; font-size: 12px;
                background: transparent; border: none;
            """)
            widgets["btn"].setStyleSheet(f"""
                QPushButton {{
                    background-color: {accent};
                    color: {btn_text_color};
                    border: none;
                    border-radius: 7px;
                    font-size: 13px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {accent_hover};
                }}
                QPushButton:pressed {{
                    background-color: {accent_hover};
                }}
            """)