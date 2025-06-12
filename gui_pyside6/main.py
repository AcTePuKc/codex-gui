from __future__ import annotations

import sys
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
)

from .backend.settings_manager import load_settings
from .backend.agent_manager import AgentManager
from .ui import MainWindow


class ApiKeyDialog(QDialog):
    """Simple dialog to request an OpenAI API key from the user."""

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
        """Return the text entered by the user."""
        return self.key_edit.text().strip()


def main() -> None:
    """Entry point for the Hybrid PySide6 GUI."""
    app = QApplication(sys.argv)

    settings = load_settings()
    agent_manager = AgentManager()
    agent_manager.set_active_agent(settings.get("selected_agent", ""))

    window = MainWindow(agent_manager, settings)
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
