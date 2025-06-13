from __future__ import annotations

import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)

from ..utils.api_key import _load_keys, _save_key, KEY_FILE, CONFIG_DIR
from .api_key_dialog import ApiKeyDialog


class ApiKeysDialog(QDialog):
    """Dialog for viewing and editing stored API keys."""

    def __init__(self, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Manage API Keys")
        self.keys: dict[str, str] = _load_keys()

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.update_btn = QPushButton("Update")
        self.delete_btn = QPushButton("Delete")
        self.close_btn = QPushButton("Close")
        btn_row.addWidget(self.update_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self.update_btn.clicked.connect(self.update_key)
        self.delete_btn.clicked.connect(self.delete_key)
        self.close_btn.clicked.connect(self.accept)

        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for provider in sorted(self.keys):
            item = QListWidgetItem(provider)
            item.setData(Qt.UserRole, provider)
            self.list_widget.addItem(item)

    def selected_provider(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def update_key(self) -> None:
        provider = self.selected_provider()
        if not provider:
            QMessageBox.information(self, "No Selection", "Please select a provider.")
            return
        dialog = ApiKeyDialog(self)
        dialog.setWindowTitle(f"{provider.capitalize()} API Key")
        dialog.key_edit.setText(self.keys.get(provider, ""))
        dialog.remember_check.setChecked(True)
        if dialog.exec() == QDialog.Accepted:
            key = dialog.api_key()
            if key:
                _save_key(provider, key)
                self.keys[provider] = key
                self.refresh_list()

    def delete_key(self) -> None:
        provider = self.selected_provider()
        if not provider:
            QMessageBox.information(self, "No Selection", "Please select a provider.")
            return
        if (
            QMessageBox.question(
                self,
                "Delete API Key",
                f"Delete stored key for {provider}?",
            )
            != QMessageBox.Yes
        ):
            return
        self.keys.pop(provider, None)
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with KEY_FILE.open("w", encoding="utf-8") as fh:
                json.dump(self.keys, fh, indent=2)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "Delete Failed", str(exc))
            return
        self.refresh_list()
