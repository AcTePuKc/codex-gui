from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
    QDialogButtonBox,
    QLineEdit,
    QLabel,
)


class ProviderEditDialog(QDialog):
    """Dialog for adding or editing a provider entry."""

    def __init__(self, key: str = "", data: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Provider" if data else "Add Provider")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Identifier:"))
        self.key_edit = QLineEdit(key)
        layout.addWidget(self.key_edit)

        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(data.get("name", "") if data else "")
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Base URL:"))
        self.base_edit = QLineEdit(data.get("baseURL", "") if data else "")
        layout.addWidget(self.base_edit)

        layout.addWidget(QLabel("Env Var Key:"))
        self.env_edit = QLineEdit(data.get("envKey", "") if data else "")
        layout.addWidget(self.env_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def provider_key(self) -> str:
        return self.key_edit.text().strip()

    def provider_info(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "baseURL": self.base_edit.text().strip(),
            "envKey": self.env_edit.text().strip(),
        }


class ProviderManagerDialog(QDialog):
    """Dialog for managing provider mappings."""

    def __init__(self, providers: dict, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Provider Manager")
        self.providers = providers

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.close_btn = QPushButton("Close")
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self.add_btn.clicked.connect(self.add_provider)
        self.edit_btn.clicked.connect(self.edit_provider)
        self.delete_btn.clicked.connect(self.delete_provider)
        self.close_btn.clicked.connect(self.accept)

        self.refresh_list()

    def refresh_list(self) -> None:
        self.list_widget.clear()
        for key, info in sorted(self.providers.items()):
            name = info.get("name", key)
            item = QListWidgetItem(f"{key} - {name}")
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)

    def selected_key(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def add_provider(self) -> None:
        dialog = ProviderEditDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            key = dialog.provider_key()
            if not key:
                QMessageBox.warning(self, "Invalid Identifier", "Identifier is required")
                return
            self.providers[key] = dialog.provider_info()
            self.refresh_list()

    def edit_provider(self) -> None:
        key = self.selected_key()
        if not key:
            QMessageBox.information(self, "No Selection", "Please select a provider.")
            return
        data = self.providers.get(key, {})
        dialog = ProviderEditDialog(key, data, self)
        if dialog.exec() == QDialog.Accepted:
            new_key = dialog.provider_key()
            if not new_key:
                QMessageBox.warning(self, "Invalid Identifier", "Identifier is required")
                return
            info = dialog.provider_info()
            if new_key != key:
                self.providers.pop(key, None)
            self.providers[new_key] = info
            self.refresh_list()

    def delete_provider(self) -> None:
        key = self.selected_key()
        if not key:
            QMessageBox.information(self, "No Selection", "Please select a provider.")
            return
        if (
            QMessageBox.question(
                self,
                "Delete Provider",
                f"Delete provider {key}?",
            )
            != QMessageBox.Yes
        ):
            return
        self.providers.pop(key, None)
        self.refresh_list()
