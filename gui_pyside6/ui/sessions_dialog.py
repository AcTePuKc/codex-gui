from __future__ import annotations

from datetime import datetime

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

from ..utils.sessions import SessionMeta


class SessionsDialog(QDialog):
    """Dialog for selecting a past session to view or resume."""

    def __init__(self, sessions: list[SessionMeta], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Browse Sessions")
        self.selected_path: str | None = None
        self.mode: str | None = None  # "view" or "resume"

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for s in sessions:
            ts = ""
            if s.timestamp:
                try:
                    ts = datetime.fromisoformat(s.timestamp).strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    ts = s.timestamp
            label = f"{ts} · {s.user_messages} msgs/{s.tool_calls} tools · {s.first_message}"
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, s.path)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.view_btn = QPushButton("View")
        self.resume_btn = QPushButton("Resume")
        self.close_btn = QPushButton("Close")
        btn_row.addWidget(self.view_btn)
        btn_row.addWidget(self.resume_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

        self.view_btn.clicked.connect(self.on_view)
        self.resume_btn.clicked.connect(self.on_resume)
        self.close_btn.clicked.connect(self.reject)

    def selected_item_path(self) -> str | None:
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item else None

    def on_view(self) -> None:
        path = self.selected_item_path()
        if not path:
            QMessageBox.information(self, "No Selection", "Please select a session.")
            return
        self.selected_path = path
        self.mode = "view"
        self.accept()

    def on_resume(self) -> None:
        path = self.selected_item_path()
        if not path:
            QMessageBox.information(self, "No Selection", "Please select a session.")
            return
        self.selected_path = path
        self.mode = "resume"
        self.accept()
