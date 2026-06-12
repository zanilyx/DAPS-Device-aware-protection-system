import sys
from pathlib import Path

# Dynamically find the root directory (parent of the folder main.py is in)
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QPushButton
from GUI_modules.Login_page_GUI import LoginPage



class DashboardPage(QWidget):
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
            f"Role: {user_data['role']}\n"
            f"Department: {user_data['department'] or 'None'}"
        )


class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modular System Application")
        self.resize(400, 300)

        # Main stack navigation matrix
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize pages
        self.login_page = LoginPage()
        self.dashboard_page = DashboardPage()

        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.dashboard_page)

        # Connect login success signal to the window router
        self.login_page.login_success.connect(self.navigate_to_dashboard)

    def navigate_to_dashboard(self, user_data: dict):
        """Switches view to dashboard and passes along user details."""
        self.dashboard_page.set_user_info(user_data)
        self.stacked_widget.setCurrentWidget(self.dashboard_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())