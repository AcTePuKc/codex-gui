from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QDoubleSpinBox,
    QSpinBox,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QCheckBox,
    QWidget,
)

from ..backend.settings_manager import save_settings
from ..backend.model_manager import get_available_models


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

        layout.addWidget(QLabel("Top-p:"))
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.1)
        self.top_p_spin.setValue(float(settings.get("top_p", 1.0)))
        layout.addWidget(self.top_p_spin)

        layout.addWidget(QLabel("Frequency Penalty:"))
        self.freq_spin = QDoubleSpinBox()
        self.freq_spin.setRange(-2.0, 2.0)
        self.freq_spin.setSingleStep(0.1)
        self.freq_spin.setValue(float(settings.get("frequency_penalty", 0.0)))
        layout.addWidget(self.freq_spin)

        layout.addWidget(QLabel("Presence Penalty:"))
        self.presence_spin = QDoubleSpinBox()
        self.presence_spin.setRange(-2.0, 2.0)
        self.presence_spin.setSingleStep(0.1)
        self.presence_spin.setValue(float(settings.get("presence_penalty", 0.0)))
        layout.addWidget(self.presence_spin)

        layout.addWidget(QLabel("Max Tokens:"))
        self.max_spin = QSpinBox()
        self.max_spin.setRange(1, 4096)
        self.max_spin.setValue(int(settings.get("max_tokens", 1024)))
        layout.addWidget(self.max_spin)

        layout.addWidget(QLabel("Provider:"))
        self.provider_edit = QLineEdit()
        self.provider_edit.setText(settings.get("provider", "openai"))
        layout.addWidget(self.provider_edit)
        self.provider_edit.editingFinished.connect(self.load_models)

        layout.addWidget(QLabel("Model:"))
        model_row = QWidget()
        model_layout = QHBoxLayout(model_row)
        model_layout.setContentsMargins(0, 0, 0, 0)
        self.model_combo = QComboBox()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.load_models)
        model_layout.addWidget(self.model_combo)
        model_layout.addWidget(refresh_btn)
        layout.addWidget(model_row)
        self.load_models()

        layout.addWidget(QLabel("Approval Mode:"))
        self.approval_combo = QComboBox()
        self.approval_combo.addItems(["suggest", "auto-edit", "full-auto"])
        self.approval_combo.setCurrentText(settings.get("approval_mode", "suggest"))
        layout.addWidget(self.approval_combo)

        self.auto_edit_check = QCheckBox("Auto Edit")
        self.auto_edit_check.setChecked(bool(settings.get("auto_edit", False)))
        layout.addWidget(self.auto_edit_check)

        self.full_auto_check = QCheckBox("Full Auto")
        self.full_auto_check.setChecked(bool(settings.get("full_auto", False)))
        layout.addWidget(self.full_auto_check)

        layout.addWidget(QLabel("Reasoning Effort:"))
        self.reason_combo = QComboBox()
        self.reason_combo.addItems(["low", "medium", "high"])
        self.reason_combo.setCurrentText(settings.get("reasoning", "high"))
        layout.addWidget(self.reason_combo)

        self.flex_check = QCheckBox("Flex Mode")
        self.flex_check.setChecked(bool(settings.get("flex_mode", False)))
        layout.addWidget(self.flex_check)

        self.quiet_check = QCheckBox("Quiet Mode")
        self.quiet_check.setChecked(bool(settings.get("quiet", False)))
        layout.addWidget(self.quiet_check)

        self.full_context_check = QCheckBox("Full Context")
        self.full_context_check.setChecked(bool(settings.get("full_context", False)))
        layout.addWidget(self.full_context_check)

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

        self.verbose_check = QCheckBox("Verbose")
        self.verbose_check.setChecked(bool(settings.get("verbose", False)))
        layout.addWidget(self.verbose_check)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def load_models(self) -> None:
        """Populate the model combo box from the selected provider."""
        provider = self.provider_edit.text().strip() or "openai"
        try:
            models = get_available_models(provider)
        except Exception:
            models = []

        current = self.settings.get("model", "")
        self.model_combo.clear()
        if models:
            self.model_combo.addItems(models)
        if current:
            index = self.model_combo.findText(current)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
            elif not models:
                self.model_combo.addItem(current)
                self.model_combo.setCurrentIndex(0)

    def accept(self) -> None:  # type: ignore[override]
        self.settings["temperature"] = float(self.temp_spin.value())
        self.settings["top_p"] = float(self.top_p_spin.value())
        self.settings["frequency_penalty"] = float(self.freq_spin.value())
        self.settings["presence_penalty"] = float(self.presence_spin.value())
        self.settings["max_tokens"] = int(self.max_spin.value())
        self.settings["provider"] = self.provider_edit.text().strip()
        self.settings["model"] = self.model_combo.currentText().strip()
        self.settings["approval_mode"] = self.approval_combo.currentText()
        self.settings["auto_edit"] = self.auto_edit_check.isChecked()
        self.settings["full_auto"] = self.full_auto_check.isChecked()
        self.settings["reasoning"] = self.reason_combo.currentText()
        self.settings["flex_mode"] = self.flex_check.isChecked()
        self.settings["quiet"] = self.quiet_check.isChecked()
        self.settings["full_context"] = self.full_context_check.isChecked()
        self.settings["cli_path"] = self.cli_edit.text().strip()
        self.settings["verbose"] = self.verbose_check.isChecked()
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
