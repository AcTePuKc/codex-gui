from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QWidget,
    QPushButton,
    QHBoxLayout,
    QInputDialog,
)

from ..backend.agent_loader import AGENTS_DIR
from ..backend.agent_manager import AgentManager


class AgentEditorDialog(QDialog):
    """Dialog for creating or editing agent JSON files."""

    def __init__(
        self, agent: dict | None = None, parent: QWidget | None = None
    ) -> None:
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
        self.json_btn = buttons.addButton("Edit JSON...", QDialogButtonBox.ActionRole)
        buttons.accepted.connect(self.save_agent)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.json_btn.clicked.connect(self.open_json_editor)

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

    def open_json_editor(self) -> None:
        data = self.gather_data()
        if self.agent_path:
            data["_path"] = str(self.agent_path)
        dlg = AgentJsonDialog(data, parent=self)
        if dlg.exec() and dlg.modified:
            self.agent_path = dlg.agent_path
            data = dlg.agent_data
            self.name_edit.setText(data.get("name", ""))
            self.desc_edit.setText(data.get("description", ""))
            self.prompt_edit.setPlainText(data.get("system_prompt", ""))
            self.temp_spin.setValue(float(data.get("default_temperature", 0.5)))
            self.tools_check.setChecked(bool(data.get("tools_enabled", False)))
            self.max_spin.setValue(int(data.get("max_tokens", 1024)))
            self.top_p_spin.setValue(float(data.get("top_p", 1.0)))
            self.freq_spin.setValue(float(data.get("frequency_penalty", 0.0)))
            self.presence_spin.setValue(float(data.get("presence_penalty", 0.0)))

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


class AgentJsonDialog(QDialog):
    """Simple JSON editor for an agent."""

    def __init__(self, agent: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.agent_data = {k: v for k, v in agent.items() if k != "_path"}
        self.agent_path: Path | None = Path(agent["_path"]) if "_path" in agent else None
        self.manager = AgentManager()
        self.setWindowTitle("Agent JSON")

        layout = QVBoxLayout(self)
        self.edit = QPlainTextEdit(json.dumps(self.agent_data, indent=2))
        layout.addWidget(self.edit)

        row = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_as_btn = QPushButton("Save As")
        self.rename_btn = QPushButton("Rename")
        self.delete_btn = QPushButton("Delete")
        self.close_btn = QPushButton("Close")
        row.addWidget(self.save_btn)
        row.addWidget(self.save_as_btn)
        row.addWidget(self.rename_btn)
        row.addWidget(self.delete_btn)
        row.addStretch(1)
        row.addWidget(self.close_btn)
        layout.addLayout(row)

        self.save_btn.clicked.connect(self.on_save)
        self.save_as_btn.clicked.connect(self.on_save_as)
        self.rename_btn.clicked.connect(self.on_rename)
        self.delete_btn.clicked.connect(self.on_delete)
        self.close_btn.clicked.connect(self.reject)

        if self.agent_path and self.manager.is_default({"_path": str(self.agent_path)}):
            self.rename_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.save_btn.setEnabled(False)

        self.modified = False

    def _parse_json(self) -> dict | None:
        try:
            return json.loads(self.edit.toPlainText())
        except json.JSONDecodeError as exc:
            QMessageBox.warning(self, "Invalid JSON", str(exc))
            return None

    def on_save(self) -> None:
        if not self.agent_path:
            self.on_save_as()
            return
        data = self._parse_json()
        if data is None:
            return
        self.agent_data = data
        AgentManager().save_agent({**data, "_path": str(self.agent_path)})
        self.modified = True

    def on_save_as(self) -> None:
        data = self._parse_json()
        if data is None:
            return
        default = data.get("name", "agent").lower().replace(" ", "_")
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Agent As",
            str(AGENTS_DIR / f"{default}.json"),
            "JSON Files (*.json)",
        )
        if not file_path:
            return
        self.agent_path = Path(file_path)
        self.agent_data = data
        AgentManager().save_agent({**data, "_path": str(self.agent_path)})
        self.modified = True

    def on_rename(self) -> None:
        if not self.agent_path:
            return
        new_name, ok = QInputDialog.getText(self, "Rename Agent", "New file name:", text=self.agent_path.stem)
        if not ok or not new_name:
            return
        new_path = self.agent_path.with_name(new_name + ".json")
        AgentManager().rename_agent({"_path": str(self.agent_path)}, new_path)
        self.agent_path = new_path
        self.modified = True

    def on_delete(self) -> None:
        if not self.agent_path:
            return
        if QMessageBox.question(
            self,
            "Delete Agent",
            f"Delete {self.agent_path.name}?",
        ) != QMessageBox.Yes:
            return
        AgentManager().delete_agent({"_path": str(self.agent_path)})
        self.modified = True
        self.accept()

