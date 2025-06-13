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
    QScrollArea,
    QWidget,
    QMessageBox,
)

import json
import os
import shutil
import subprocess
from pathlib import Path
from urllib import request

from ..backend.settings_manager import save_settings
from ..backend.model_manager import get_available_models
from ..backend import codex_adapter
from ..utils.api_key import ensure_api_key
from .api_keys_dialog import ApiKeysDialog
from .. import logger


class SettingsDialog(QDialog):
    """Dialog for modifying runtime settings."""

    def __init__(self, settings: dict, parent: QWidget | None = None, debug_console=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.debug_console = debug_console
        self.setWindowTitle("Settings")

        self.resize(480, 600)

        main_layout = QVBoxLayout(self)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

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
        provider_row = QWidget()
        provider_layout = QHBoxLayout(provider_row)
        provider_layout.setContentsMargins(0, 0, 0, 0)
        self.provider_combo = QComboBox()
        self.manage_keys_btn = QPushButton("Manage API Keys")
        self.manage_providers_btn = QPushButton("Manage Providers")
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addWidget(self.manage_keys_btn)
        provider_layout.addWidget(self.manage_providers_btn)
        self.refresh_providers()
        layout.addWidget(provider_row)
        self.provider_combo.currentIndexChanged.connect(
            lambda: self.load_models(prompt_for_key=True)
        )
        self.manage_keys_btn.clicked.connect(self.manage_api_keys)
        self.manage_providers_btn.clicked.connect(self.manage_providers)

        layout.addWidget(QLabel("Model:"))
        model_row = QWidget()
        model_layout = QHBoxLayout(model_row)
        model_layout.setContentsMargins(0, 0, 0, 0)
        self.model_combo = QComboBox()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(lambda: self.load_models(prompt_for_key=True))
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
        check_btn = QPushButton("Check")
        check_btn.clicked.connect(self.check_cli)
        cli_layout.addWidget(self.cli_edit)
        cli_layout.addWidget(browse_btn)
        cli_layout.addWidget(check_btn)
        layout.addWidget(cli_row)

        self.verbose_check = QCheckBox("Verbose")
        self.verbose_check.setChecked(bool(settings.get("verbose", False)))
        layout.addWidget(self.verbose_check)

        self.notify_check = QCheckBox("Notify")
        self.notify_check.setChecked(bool(settings.get("notify", False)))
        layout.addWidget(self.notify_check)

        self.no_project_doc_check = QCheckBox("No Project Doc")
        self.no_project_doc_check.setChecked(
            bool(settings.get("no_project_doc", False))
        )
        layout.addWidget(self.no_project_doc_check)

        self.disable_storage_check = QCheckBox("Disable Response Storage")
        self.disable_storage_check.setChecked(
            bool(settings.get("disable_response_storage", False))
        )
        layout.addWidget(self.disable_storage_check)

        self.auto_scan_check = QCheckBox("Auto Scan Files")
        self.auto_scan_check.setChecked(
            bool(settings.get("auto_scan_files", True))
        )
        layout.addWidget(self.auto_scan_check)

        layout.addWidget(QLabel("Project Doc:"))
        project_doc_row = QWidget()
        project_doc_layout = QHBoxLayout(project_doc_row)
        project_doc_layout.setContentsMargins(0, 0, 0, 0)
        self.project_doc_edit = QLineEdit()
        self.project_doc_edit.setText(settings.get("project_doc", ""))
        project_doc_btn = QPushButton("Browse")
        project_doc_btn.clicked.connect(self.browse_project_doc)
        project_doc_layout.addWidget(self.project_doc_edit)
        project_doc_layout.addWidget(project_doc_btn)
        layout.addWidget(project_doc_row)

        layout.addWidget(QLabel("Writable Root:"))
        writable_row = QWidget()
        writable_layout = QHBoxLayout(writable_row)
        writable_layout.setContentsMargins(0, 0, 0, 0)
        self.writable_root_edit = QLineEdit()
        self.writable_root_edit.setText(settings.get("writable_root", ""))
        writable_btn = QPushButton("Browse")
        writable_btn.clicked.connect(self.browse_writable_root)
        writable_layout.addWidget(self.writable_root_edit)
        writable_layout.addWidget(writable_btn)
        layout.addWidget(writable_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def load_models(self, prompt_for_key: bool = False) -> None:
        """Populate the model combo box based on the selected provider."""
        providers = self.settings.get("providers", {})
        provider = self.provider_combo.currentData() or "openai"
        info = providers.get(provider, {})
        env_var = info.get("envKey") or f"{provider.upper()}_API_KEY"
        if provider not in {"local", "custom"} and env_var:
            has_key = os.getenv(env_var) or os.getenv("OPENAI_API_KEY")
            if not has_key:
                if prompt_for_key:
                    if not ensure_api_key(provider, self):
                        self.model_combo.clear()
                        return
                else:
                    self.model_combo.clear()
                    return
        if provider not in {"local", "custom"}:
            try:
                models = get_available_models(provider)
            except Exception:
                models = []
        elif provider in {"local", "custom"}:
            models = []
            if provider == "local":
                if shutil.which("ollama"):
                    commands = [["ollama", "list", "--json"], ["ollama", "ls", "--json"]]
                    for cmd in commands:
                        logger.info("$ " + " ".join(cmd))
                        try:
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=5,
                                check=False,
                            )
                            if result.stderr:
                                for line in result.stderr.splitlines():
                                    logger.error(line)
                            for line in result.stdout.splitlines():
                                try:
                                    data = json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                                name = data.get("name")
                                if isinstance(name, str):
                                    models.append(name)
                            if models:
                                break
                        except Exception as exc:  # pylint: disable=broad-except
                            logger.error(str(exc))

                    cmd = ["ollama", "ps", "--json"]
                    logger.info("$ " + " ".join(cmd))
                    try:
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            timeout=5,
                            check=False,
                        )
                        stderr_lower = (result.stderr or "").lower()
                        unknown_flag = "unknown flag" in stderr_lower
                        if unknown_flag or result.returncode != 0:
                            if result.stderr:
                                for line in result.stderr.splitlines():
                                    if "unknown flag" not in line.lower():
                                        logger.error(line)
                            cmd = ["ollama", "ps"]
                            logger.info("$ " + " ".join(cmd))
                            result = subprocess.run(
                                cmd,
                                capture_output=True,
                                text=True,
                                timeout=5,
                                check=False,
                            )
                            if result.stderr:
                                for line in result.stderr.splitlines():
                                    logger.error(line)
                            for line in result.stdout.splitlines():
                                line = line.strip()
                                if not line or line.lower().startswith("name"):
                                    continue
                                logger.info(line)
                        else:
                            for line in result.stderr.splitlines():
                                logger.error(line)
                            for line in result.stdout.splitlines():
                                try:
                                    data = json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                                name = data.get("name")
                                status = data.get("status")
                                if name:
                                    msg = f"Running model: {name}"
                                    if status:
                                        msg += f" ({status})"
                                    logger.info(msg)
                    except Exception as exc:  # pylint: disable=broad-except
                        logger.error(str(exc))

                if not models:
                    search_paths = [
                        Path(os.getenv("LOCAL_MODELS_DIR", "")),
                        Path.home() / ".codex" / "models",
                        Path.cwd() / "models",
                    ]
                    valid_ext = {".bin", ".gguf"}
                    for base in search_paths:
                        if not base:
                            continue
                        try:
                            for entry in base.expanduser().iterdir():
                                if entry.is_dir():
                                    if any(
                                        f.suffix.lower() in valid_ext
                                        for f in entry.iterdir()
                                        if f.is_file()
                                    ):
                                        models.append(entry.name)
                                elif (
                                    entry.is_file()
                                    and entry.suffix.lower() in valid_ext
                                ):
                                    models.append(entry.stem)
                        except FileNotFoundError:
                            continue
                    models = sorted(set(models))
            else:
                base_url = os.getenv("CUSTOM_MODELS_URL") or os.getenv(
                    "CUSTOM_BASE_URL"
                )
                if base_url and not base_url.endswith("/models"):
                    endpoint = base_url.rstrip("/") + "/models"
                else:
                    endpoint = base_url
                if endpoint:
                    try:
                        with request.urlopen(endpoint, timeout=5) as resp:
                            data = json.load(resp)
                        items = data.get("data", data)
                        for item in items:
                            model_id = (
                                item.get("id") if isinstance(item, dict) else item
                            )
                            if isinstance(model_id, str):
                                if model_id.startswith("models/"):
                                    model_id = model_id.replace("models/", "")
                                models.append(model_id)
                        models = sorted(set(models))
                    except Exception:
                        models = []
        else:
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
        self.settings["provider"] = self.provider_combo.currentData() or "openai"
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
        self.settings["notify"] = self.notify_check.isChecked()
        self.settings["no_project_doc"] = self.no_project_doc_check.isChecked()
        self.settings["disable_response_storage"] = (
            self.disable_storage_check.isChecked()
        )
        self.settings["project_doc"] = self.project_doc_edit.text().strip()
        self.settings["writable_root"] = self.writable_root_edit.text().strip()
        self.settings["auto_scan_files"] = self.auto_scan_check.isChecked()
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

    def check_cli(self) -> None:
        """Verify the Codex CLI path and log search details."""
        def log_fn(text: str, level: str = "info") -> None:
            if level == "error":
                logger.error(text)
            else:
                logger.info(text)

        tmp_settings = self.settings.copy()
        tmp_settings["cli_path"] = self.cli_edit.text().strip()
        try:
            codex_adapter.ensure_cli_available(tmp_settings, log_fn=log_fn)
        except FileNotFoundError as exc:
            logger.error(str(exc))
            QMessageBox.warning(self, "Codex CLI Missing", str(exc))
            return

        self.cli_edit.setText(tmp_settings.get("cli_path", ""))
        QMessageBox.information(self, "Codex CLI Found", f"Using CLI at: {tmp_settings.get('cli_path', '')}")

    def browse_project_doc(self) -> None:
        """Prompt the user to select an additional project doc file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Project Doc",
            str(self.project_doc_edit.text() or ""),
        )
        if filename:
            self.project_doc_edit.setText(filename)

    def browse_writable_root(self) -> None:
        """Prompt the user to select the writable root directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Writable Root",
            str(self.writable_root_edit.text() or ""),
        )
        if directory:
            self.writable_root_edit.setText(directory)

    def manage_api_keys(self) -> None:
        """Open the API key manager dialog."""
        ApiKeysDialog(self).exec()

    def manage_providers(self) -> None:
        """Open the provider manager dialog."""
        from .provider_manager_dialog import ProviderManagerDialog

        dialog = ProviderManagerDialog(self.settings.get("providers", {}), self)
        if dialog.exec():
            save_settings(self.settings)
            self.refresh_providers()
            self.load_models(prompt_for_key=True)

    def refresh_providers(self) -> None:
        """Populate the provider combo from settings."""
        self.provider_combo.clear()
        providers = self.settings.get("providers", {})
        for key, info in sorted(providers.items()):
            name = info.get("name", key)
            self.provider_combo.addItem(name, key)
        current = self.settings.get("provider", "openai")
        index = self.provider_combo.findData(current)
        if index >= 0:
            self.provider_combo.setCurrentIndex(index)
