from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class HomePage(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        label = QLabel("HOME PAGE")
        layout.addWidget(label)

        self.setLayout(layout)