from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from .backend.settings_manager import load_settings
from .backend.agent_manager import AgentManager
from .ui import MainWindow

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
