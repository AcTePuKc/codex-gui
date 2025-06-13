from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPalette
from PySide6.QtCore import Qt

from .backend.settings_manager import load_settings
from .backend.agent_manager import AgentManager
from .ui import MainWindow


def apply_theme(app: QApplication, theme: str) -> None:
    """Apply light or dark theme to the application."""
    if theme == "Dark":
        app.setStyle("Fusion")
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.black)
        app.setPalette(palette)
    elif theme == "Light":
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())

def main() -> None:
    """Entry point for the Hybrid PySide6 GUI."""
    app = QApplication(sys.argv)

    settings = load_settings()
    apply_theme(app, settings.get("theme", "System"))
    agent_manager = AgentManager()
    agent_manager.set_active_agent(settings.get("selected_agent", ""))

    window = MainWindow(agent_manager, settings)
    window.resize(800, 600)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
