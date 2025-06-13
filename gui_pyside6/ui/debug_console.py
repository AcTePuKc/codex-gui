from __future__ import annotations

from PySide6.QtWidgets import (
    QDockWidget,
    QPlainTextEdit,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QPushButton,
)
import logging

from PySide6.QtCore import Qt

from .. import logger


class DebugConsole(QDockWidget):
    """Dockable widget that displays log output."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Debug Console", parent)
        self.setAllowedAreas(Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        layout.addWidget(self.view)

        row = QHBoxLayout()
        self.info_check = QCheckBox("Info")
        self.info_check.setChecked(True)
        self.info_check.toggled.connect(self._refresh_view)
        self.error_check = QCheckBox("Errors")
        self.error_check.setChecked(True)
        self.error_check.toggled.connect(self._refresh_view)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.clear)
        row.addWidget(self.info_check)
        row.addWidget(self.error_check)
        row.addStretch(1)
        row.addWidget(clear_btn)
        layout.addLayout(row)

        self._entries: list[tuple[str, str]] = []  # (level, text)

        self.setWidget(container)

        class _LogHandler(logging.Handler):
            def __init__(self, console: DebugConsole) -> None:
                super().__init__()
                self.console = console

            def emit(self, record: logging.LogRecord) -> None:
                msg = self.format(record)
                level = "error" if record.levelno >= logging.ERROR else "info"
                self.console.append(msg, level)

        self._handler = _LogHandler(self)
        self._handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(self._handler)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        logger.removeHandler(self._handler)
        super().closeEvent(event)

    def append(self, text: str, level: str = "info") -> None:
        self._entries.append((level, text))
        self._refresh_view()

    def append_info(self, text: str) -> None:
        self.append(text, "info")

    def append_error(self, text: str) -> None:
        self.append(text, "error")

    def clear(self) -> None:  # type: ignore[override]
        self._entries.clear()
        self.view.clear()

    def _refresh_view(self) -> None:
        show_info = self.info_check.isChecked()
        show_err = self.error_check.isChecked()
        lines: list[str] = []
        for level, text in self._entries:
            if (level == "info" and show_info) or (level == "error" and show_err):
                lines.append(text)
        self.view.setPlainText("\n".join(lines))
        self.view.verticalScrollBar().setValue(self.view.verticalScrollBar().maximum())
