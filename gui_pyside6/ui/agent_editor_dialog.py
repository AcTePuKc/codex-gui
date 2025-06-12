from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QWidget,
)

from ..backend.agent_loader import AGENTS_DIR


class AgentEditorDialog(QDialog):
    """Dialog for creating or editing agent JSON files."""

    def __init__(self, agent: dict | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.agent_path: Path | None = None
        data = agent or {}
        if "_path" in data:
            self.agent_path = Path(data.pop("_path"))
        self.setWindowTitle("Edit Agent" if agent else "New Agent")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(data.get("name", ""))
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Description:"))
        self.desc_edit = QLineEdit(data.get("description", ""))
        layout.addWidget(self.desc_edit)

        layout.addWidget(QLabel("System Prompt:"))
        self.prompt_edit = QPlainTextEdit(data.get("system_prompt", ""))
        layout.addWidget(self.prompt_edit)

        layout.addWidget(QLabel("Temperature:"))
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(float(data.get("default_temperature", 0.5)))
        layout.addWidget(self.temp_spin)

        self.tools_check = QCheckBox("Tools Enabled")
        self.tools_check.setChecked(bool(data.get("tools_enabled", False)))
        layout.addWidget(self.tools_check)

        layout.addWidget(QLabel("Max Tokens:"))
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 4096)
        self.max_spin.setValue(int(data.get("max_tokens", 1024)))
        layout.addWidget(self.max_spin)

        layout.addWidget(QLabel("Top-p:"))
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.1)
        self.top_p_spin.setValue(float(data.get("top_p", 1.0)))
        layout.addWidget(self.top_p_spin)

        layout.addWidget(QLabel("Frequency Penalty:"))
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(-2.0, 2.0)
        self.freq_spin.setSingleStep(0.1)
        self.freq_spin.setValue(float(data.get("frequency_penalty", 0.0)))
        layout.addWidget(self.freq_spin)

        layout.addWidget(QLabel("Presence Penalty:"))
        self.presence_spin = QDoubleSpinBox()
        self.presence_spin.setRange(-2.0, 2.0)
        self.presence_spin.setSingleStep(0.1)
        self.presence_spin.setValue(float(data.get("presence_penalty", 0.0)))
        layout.addWidget(self.presence_spin)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.save_agent)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def gather_data(self) -> dict[str, Any]:
        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.text().strip(),
            "system_prompt": self.prompt_edit.toPlainText(),
            "default_temperature": float(self.temp_spin.value()),
            "tools_enabled": self.tools_check.isChecked(),
            "max_tokens": int(self.max_spin.value()),
            "top_p": float(self.top_p_spin.value()),
            "frequency_penalty": float(self.freq_spin.value()),
            "presence_penalty": float(self.presence_spin.value()),
        }

    def save_agent(self) -> None:
        data = self.gather_data()
        path = self.agent_path
        if path is None:
            default = data["name"].lower().replace(" ", "_") or "agent"
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Agent",
                str(AGENTS_DIR / f"{default}.json"),
                "JSON Files (*.json)",
            )
            if not file_path:
                return
            path = Path(file_path)
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "Save Failed", str(exc))
            return
        self.agent_path = path
        self.accept()
