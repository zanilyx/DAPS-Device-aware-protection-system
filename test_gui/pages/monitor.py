from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class MonitorPage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        label = QLabel("MONITOR PAGE")
        layout.addWidget(label)

        self.setLayout(layout)