from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QSpinBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QWidget,
)

from ..backend.settings_manager import save_settings


class SettingsDialog(QDialog):
    """Dialog for modifying runtime settings."""

    def __init__(self, settings: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Temperature:"))
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.0)
        self.temp_spin.setSingleStep(0.1)
        self.temp_spin.setValue(float(settings.get("temperature", 0.5)))
        layout.addWidget(self.temp_spin)

        layout.addWidget(QLabel("Max Tokens:"))
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 4096)
        self.max_spin.setValue(int(settings.get("max_tokens", 1024)))
        layout.addWidget(self.max_spin)

        layout.addWidget(QLabel("Codex CLI Path:"))
        cli_row = QWidget()
        cli_layout = QHBoxLayout(cli_row)
        cli_layout.setContentsMargins(0, 0, 0, 0)
        self.cli_edit = QLineEdit()
        self.cli_edit.setText(settings.get("cli_path", ""))
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_cli)
        cli_layout.addWidget(self.cli_edit)
        cli_layout.addWidget(browse_btn)
        layout.addWidget(cli_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self) -> None:  # type: ignore[override]
        self.settings["temperature"] = float(self.temp_spin.value())
        self.settings["max_tokens"] = int(self.max_spin.value())
        self.settings["cli_path"] = self.cli_edit.text().strip()
        save_settings(self.settings)
        super().accept()

    def browse_cli(self) -> None:
        """Prompt the user to select the Codex CLI executable."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Codex CLI",
            str(self.cli_edit.text() or ""),
        )
        if filename:
            self.cli_edit.setText(filename)

