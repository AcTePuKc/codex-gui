from __future__ import annotations

from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


class ApiKeyDialog(QDialog):
    """Dialog to request an API key for a provider."""

    def __init__(self, provider: str, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        provider_title = provider.capitalize()
        self.setWindowTitle(f"Enter {provider_title} API Key")

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Please enter your {provider_title} API key:"))

        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.key_edit)

        self.remember_check = QCheckBox("Remember key")
        layout.addWidget(self.remember_check)

        self.get_key_button = QPushButton("Get API Key")
        self.get_key_button.clicked.connect(
            lambda: QDesktopServices.openUrl(
                QUrl("https://platform.openai.com/account/api-keys")
            )
        )
        layout.addWidget(self.get_key_button)

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

    def remember_key(self) -> bool:
        """Return ``True`` if the remember checkbox is checked."""
        return self.remember_check.isChecked()
