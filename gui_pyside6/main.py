from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from .backend.settings_manager import load_settings
from .backend.agent_manager import AgentManager
from .ui import MainWindow


def main() -> None:
    """Entry point for the Hybrid PySide6 GUI."""
    app = QApplication(sys.argv)

    _ = load_settings()  # Load user settings for future use
    agent_manager = AgentManager()

    window = MainWindow(agent_manager)
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
