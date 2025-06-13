import os
import subprocess
import shutil

import pytest
try:
    from PySide6.QtWidgets import QApplication
except Exception as exc:  # pylint: disable=broad-except
    pytest.skip(f"PySide6 not available: {exc}", allow_module_level=True)

from gui_pyside6.ui.settings_dialog import SettingsDialog
from gui_pyside6.backend import model_manager


def test_load_models_parses_json(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    settings = {"provider": "local", "providers": {"local": {"name": "Local"}}}

    monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/ollama")

    def fake_run(cmd, capture_output=True, text=True, timeout=5, check=False):
        if cmd[:2] in (["ollama", "list"], ["ollama", "ls"]):
            stdout = '{"models": [{"name": "test-model"}]}'
        else:
            stdout = ""
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    dialog = SettingsDialog(settings)
    models = [dialog.model_combo.itemText(i) for i in range(dialog.model_combo.count())]
    assert "test-model" in models


def test_load_models_parses_plain_text(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    settings = {"provider": "local", "providers": {"local": {"name": "Local"}}}

    monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/ollama")

    def fake_run(cmd, capture_output=True, text=True, timeout=5, check=False):
        if cmd == ["ollama", "list", "--json"]:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="unknown flag: --json")
        if cmd == ["ollama", "list"]:
            stdout = "NAME ID SIZE MODIFIED\nqwen3:8b abc123 5 GB 2 days ago\n"
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        if cmd[0:2] == ["ollama", "ps"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    dialog = SettingsDialog(settings)
    models = [dialog.model_combo.itemText(i) for i in range(dialog.model_combo.count())]
    assert "qwen3:8b" in models


def test_cli_command_with_spaces_preserved(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    settings = {}

    dialog = SettingsDialog(settings)
    command = "npx codex --no-update-notifier"
    dialog.cli_edit.setText(command)
    dialog.accept()

    assert settings["cli_path"] == command


def test_ollama_ps_json_flag_cached(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    settings = {"provider": "local", "providers": {"local": {"name": "Local"}}}

    monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/ollama")
    calls = []

    def fake_run(cmd, capture_output=True, text=True, timeout=5, check=False):
        calls.append(cmd)
        if cmd[:3] == ["ollama", "list", "--json"] or cmd[:3] == ["ollama", "ls", "--json"]:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="unknown flag: --json")
        if cmd[:2] in (["ollama", "list"], ["ollama", "ls"]):
            stdout = "NAME ID SIZE\nmodel1 id1 1 GB"
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        if cmd[:2] == ["ollama", "ps"]:
            if cmd[-1] == "--json":
                return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="unknown flag: --json")
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    import gui_pyside6.ui.settings_dialog as sd
    sd._OLLAMA_PS_JSON = None
    monkeypatch.setattr(subprocess, "run", fake_run)

    dialog = SettingsDialog(settings)
    dialog.load_models()

    ps_cmds = [c for c in calls if c[:2] == ["ollama", "ps"]]
    assert ps_cmds[0] == ["ollama", "ps", "--json"]
    assert ps_cmds[1] == ["ollama", "ps"]


def test_provider_selection_persists_and_loads_models(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    settings = {
        "provider": "openai",
        "providers": {
            "openai": {"name": "OpenAI"},
            "ollama": {"name": "Ollama"},
        },
    }

    monkeypatch.setattr(model_manager, "get_available_models", lambda p: ["openai-model"])
    monkeypatch.setattr(shutil, "which", lambda x: "/usr/bin/ollama")

    def fake_run(cmd, capture_output=True, text=True, timeout=5, check=False):
        if cmd[:2] in (["ollama", "list"], ["ollama", "ls"]):
            stdout = '{"models": [{"name": "ollama-model"}]}'
            return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")
        if cmd[:2] == ["ollama", "ps"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    dialog = SettingsDialog(settings)
    assert dialog.provider_combo.currentData() == "openai"
    assert dialog.model_combo.findText("openai-model") >= 0

    index = dialog.provider_combo.findData("ollama")
    dialog.provider_combo.setCurrentIndex(index)

    assert dialog.provider_combo.currentData() == "ollama"
    assert dialog.model_combo.findText("ollama-model") >= 0

    dialog.refresh_providers()

    assert dialog.provider_combo.currentData() == "ollama"
    assert dialog.model_combo.findText("ollama-model") >= 0

def test_load_models_called_after_model_combo_created(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    settings = {"provider": "openai", "providers": {"openai": {"name": "OpenAI"}}}

    def fake_load_models(self, prompt_for_key=False):
        assert hasattr(self, "model_combo")

    monkeypatch.setattr(SettingsDialog, "load_models", fake_load_models)

    SettingsDialog(settings)


def test_api_key_dialog_get_key_button_visibility():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    from gui_pyside6.ui.api_key_dialog import ApiKeyDialog

    openai_dialog = ApiKeyDialog("openai")
    assert hasattr(openai_dialog, "get_key_button")

    ollama_dialog = ApiKeyDialog("ollama")
    assert not hasattr(ollama_dialog, "get_key_button")


def test_theme_selection_saved():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    settings = {}
    dialog = SettingsDialog(settings)
    index = dialog.theme_combo.findText("Dark")
    dialog.theme_combo.setCurrentIndex(index)
    dialog.accept()

    assert settings["theme"] == "Dark"

