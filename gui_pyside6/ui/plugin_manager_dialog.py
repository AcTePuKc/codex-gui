from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
)


class PluginManagerDialog(QDialog):
    """Dialog for enabling or disabling optional plugins."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Plugin Manager")
        self.manifest_path = (
            Path(__file__).resolve().parents[1] / "plugins" / "manifest.json"
        )
        self.plugins: list[dict] = self.load_manifest()

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for plugin in self.plugins:
            name = plugin.get("name") or plugin.get("entry", "")
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsSelectable)
            item.setCheckState(Qt.Checked if plugin.get("enabled") else Qt.Unchecked)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.enable_btn = QPushButton("Enable")
        self.disable_btn = QPushButton("Disable")
        self.save_btn = QPushButton("Save")
        self.close_btn = QPushButton("Close")
        btn_row.addWidget(self.enable_btn)
        btn_row.addWidget(self.disable_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self.enable_btn.clicked.connect(lambda: self.set_selected(True))
        self.disable_btn.clicked.connect(lambda: self.set_selected(False))
        self.save_btn.clicked.connect(self.save_changes)
        self.close_btn.clicked.connect(self.reject)

    def load_manifest(self) -> list[dict]:
        try:
            with self.manifest_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return list(data.get("plugins", []))
        except Exception:  # pylint: disable=broad-except
            return []

    def set_selected(self, enabled: bool) -> None:
        for item in self.list_widget.selectedItems():
            item.setCheckState(Qt.Checked if enabled else Qt.Unchecked)

    def save_changes(self) -> None:
        for idx in range(self.list_widget.count()):
            item = self.list_widget.item(idx)
            self.plugins[idx]["enabled"] = item.checkState() == Qt.Checked

        data = {"plugins": self.plugins}
        try:
            with self.manifest_path.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=2)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "Save Failed", str(exc))
            return

        self.accept()
