from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QVBoxLayout,
    QProgressBar,
)

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class ProgressDialog(QDialog):

    def __init__(self, title="Processing"):

        super().__init__()

        self.setWindowTitle(title)
        self.setFixedSize(430, 160)

        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.setStyleSheet("""
            QDialog{
                background:#0D1B2A;
            }

            QLabel{
                color:white;
                background:transparent;
            }

            QProgressBar{

                border:1px solid #2A4059;
                border-radius:7px;

                background:#1C2E42;

                text-align:center;

                color:white;

                height:24px;
            }

            QProgressBar::chunk{

                background:#4A9EBF;

                border-radius:6px;
            }

        """)

        layout = QVBoxLayout()

        layout.setContentsMargins(25,25,25,25)

        layout.setSpacing(15)

        self.titleLabel = QLabel(title)

        self.titleLabel.setFont(
            QFont("Segoe UI",13,QFont.Bold)
        )

        self.statusLabel = QLabel("Starting...")

        self.statusLabel.setFont(
            QFont("Segoe UI",10)
        )

        self.progress = QProgressBar()

        self.progress.setRange(0,100)

        self.progress.setValue(0)

        layout.addWidget(self.titleLabel)

        layout.addWidget(self.statusLabel)

        layout.addWidget(self.progress)

        self.setLayout(layout)

    # ---------------------------------------------

    def update_progress(self,value,message):

        self.progress.setValue(value)

        self.statusLabel.setText(message)

        self.repaint()

        self.progress.repaint()

        self.statusLabel.repaint()

        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()

    # ---------------------------------------------

    def finish(self,message="Completed Successfully"):

        self.update_progress(
            100,
            message
        )

        from PySide6.QtWidgets import QApplication

        QApplication.processEvents()