import sys
from pathlib import Path

# Dynamically find the root directory (parent of the folder main.py is in)
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget, QVBoxLayout, QLabel, QPushButton
from GUI_modules.Login_page_GUI import LoginPage
from GUI_modules.Home_GUI import HomePage


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
        self.home_page = HomePage()

        self.stacked_widget.addWidget(self.login_page)
        self.stacked_widget.addWidget(self.home_page)

        # Connect login success signal to the window router
        self.login_page.login_success.connect(self.navigate_to_dashboard)

    def navigate_to_dashboard(self, user_data: dict):
        """Switches view to dashboard and passes along user details."""
        self.home_page.set_user_info(user_data)
        self.stacked_widget.setCurrentWidget(self.home_page)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec())