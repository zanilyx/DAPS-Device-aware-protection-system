from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QRadioButton,
    QCheckBox,
    QMessageBox
)


class RoleSelectionDialog(QDialog):

    def __init__(self, owner_role):
        super().__init__()

        self.owner_role = owner_role

        self.setWindowTitle("Encryption Settings")
        self.setFixedSize(420, 430)

        self.selected_classification = None
        self.allowed_roles = []

        self.build_ui()

    def build_ui(self):

        layout = QVBoxLayout()

        # ------------------------------------------------
        # Owner
        # ------------------------------------------------

        owner = QLabel(f"<b>Owner Role :</b> {self.owner_role}")
        layout.addWidget(owner)

        # ------------------------------------------------
        # Classification
        # ------------------------------------------------

        class_group = QGroupBox("Classification")

        class_layout = QVBoxLayout()

        self.public_btn = QRadioButton("Public")
        self.internal_btn = QRadioButton("Internal")
        self.confidential_btn = QRadioButton("Confidential")

        self.confidential_btn.setChecked(True)

        class_layout.addWidget(self.public_btn)
        class_layout.addWidget(self.internal_btn)
        class_layout.addWidget(self.confidential_btn)

        class_group.setLayout(class_layout)

        layout.addWidget(class_group)

        # ------------------------------------------------
        # Allowed Roles
        # ------------------------------------------------

        role_group = QGroupBox("Allowed Roles")

        role_layout = QVBoxLayout()

        self.roles = {}

        role_names = [
            "admin",
            "manager",
            "hr",
            "finance",
            "developer"
        ]

        for role in role_names:

            cb = QCheckBox(role)

            # Owner always has access
            if role == self.owner_role:
                cb.setChecked(True)
                cb.setEnabled(False)

            self.roles[role] = cb

            role_layout.addWidget(cb)

        role_group.setLayout(role_layout)

        layout.addWidget(role_group)

        # ------------------------------------------------
        # Buttons
        # ------------------------------------------------

        button_layout = QHBoxLayout()

        encrypt_btn = QPushButton("Encrypt")
        cancel_btn = QPushButton("Cancel")

        encrypt_btn.clicked.connect(self.accept_data)
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(encrypt_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def accept_data(self):

        if self.public_btn.isChecked():
            self.selected_classification = "Public"

        elif self.internal_btn.isChecked():
            self.selected_classification = "Internal"

        else:
            self.selected_classification = "Confidential"

        self.allowed_roles = []

        for role, cb in self.roles.items():

            if cb.isChecked():
                self.allowed_roles.append(role)

        if len(self.allowed_roles) == 0:

            QMessageBox.warning(
                self,
                "Error",
                "Select at least one role."
            )
            return

        self.accept()

    def get_data(self):

        return (
            self.selected_classification,
            self.allowed_roles
        )