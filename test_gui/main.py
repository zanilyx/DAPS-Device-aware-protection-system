import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget
)

from pages.home import HomePage
from pages.monitor import MonitorPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DAPS Test")
        self.resize(900, 600)

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        central.setLayout(main_layout)

        # Top button bar
        button_layout = QHBoxLayout()

        self.home_btn = QPushButton("Home")
        self.monitor_btn = QPushButton("Monitor")

        button_layout.addWidget(self.home_btn)
        button_layout.addWidget(self.monitor_btn)

        main_layout.addLayout(button_layout)

        # Page container
        self.stack = QStackedWidget()

        self.home_page = HomePage()
        self.monitor_page = MonitorPage()

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.monitor_page)

        main_layout.addWidget(self.stack)

        # Connections
        self.home_btn.clicked.connect(self.show_home)
        self.monitor_btn.clicked.connect(self.show_monitor)

    def show_home(self):
        self.stack.setCurrentWidget(self.home_page)

    def show_monitor(self):
        self.stack.setCurrentWidget(self.monitor_page)


app = QApplication(sys.argv)

window = MainWindow()
window.show()

sys.exit(app.exec())