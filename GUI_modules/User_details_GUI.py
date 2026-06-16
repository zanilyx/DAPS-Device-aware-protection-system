from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel


class UserDetails(QWidget):
    """Placeholder for the landing page after a successful login."""
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.welcome_label = QLabel()
        self.layout.addWidget(self.welcome_label)
        self.setLayout(self.layout)

    def set_user_info(self, user_data: dict):
        self.welcome_label.setText(
            f"Welcome, {user_data['username']}!\n"
            f"Email: {user_data['email']}\n"
            f"Role: {user_data['role']}\n"
            f"Department: {user_data['department'] or 'None'}"
    )