from __future__ import annotations

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton


class ApiKeyDialog(QDialog):
    """Dialog to request an OpenAI API key from the user."""

    def __init__(self, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Enter OpenAI API Key")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Please enter your OpenAI API key:"))

        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.key_edit)

        button_layout = QVBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def api_key(self) -> str:
        """Return the entered API key."""
        return self.key_edit.text().strip()
