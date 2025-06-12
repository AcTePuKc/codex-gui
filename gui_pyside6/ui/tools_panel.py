from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QHBoxLayout,
    QPushButton,
    QPlainTextEdit,
    QLabel,
    QComboBox,
    QMessageBox,
)

from ..backend.tool_runner import run_tool_script


class ToolsPanel(QDialog):
    """Dialog listing scripts from the project tools/ directory."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Tools")

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        row = QHBoxLayout()
        row.addWidget(QLabel("Backend:"))
        self.backend_combo = QComboBox()
        self.backend_combo.addItem("(none)", None)
        for name in self.available_backends():
            self.backend_combo.addItem(name, name)
        row.addWidget(self.backend_combo)
        self.run_btn = QPushButton("Run")
        self.close_btn = QPushButton("Close")
        row.addWidget(self.run_btn)
        row.addWidget(self.close_btn)
        layout.addLayout(row)

        self.output_view = QPlainTextEdit()
        self.output_view.setReadOnly(True)
        layout.addWidget(self.output_view)

        self.run_btn.clicked.connect(self.run_selected)
        self.close_btn.clicked.connect(self.accept)

        self.load_scripts()

    def tools_dir(self) -> Path:
        return Path(__file__).resolve().parents[2] / "tools"

    def available_backends(self) -> list[str]:
        path = (
            Path(__file__).resolve().parents[1]
            / "backend"
            / "backend_requirements.json"
        )
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return list(data.keys())
        except Exception:  # pylint: disable=broad-except
            return []

    def load_scripts(self) -> None:
        self.list_widget.clear()
        tools = self.tools_dir()
        if tools.exists():
            for script in sorted(tools.glob("*.py")):
                self.list_widget.addItem(script.name)

    def run_selected(self) -> None:
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "No Selection", "Please select a script.")
            return
        script_path = self.tools_dir() / item.text()
        backend_name = self.backend_combo.currentData()
        _, stdout, stderr = run_tool_script(script_path, backend_name=backend_name)
        self.output_view.clear()
        if stdout:
            self.output_view.appendPlainText(stdout)
        if stderr:
            self.output_view.appendPlainText(stderr)
