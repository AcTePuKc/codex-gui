from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

from .backend.agent_loader import load_agents
from .backend.settings_manager import load_settings


def main() -> None:
    """Entry point for the Hybrid PySide6 GUI."""
    app = QApplication(sys.argv)

    agents = load_agents()
    settings = load_settings()

    window = QWidget()
    window.setWindowTitle("Codex-GUI")
    layout = QVBoxLayout(window)
    info = QLabel(
        f"Loaded {len(agents)} agents. Selected: {settings.get('selected_agent')}"
    )
    layout.addWidget(info)
    window.resize(400, 200)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
