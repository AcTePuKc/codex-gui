import os
import subprocess
import shutil

import pytest
try:
    from PySide6.QtWidgets import QApplication
except Exception as exc:  # pylint: disable=broad-except
    pytest.skip(f"PySide6 not available: {exc}", allow_module_level=True)

from gui_pyside6.ui.settings_dialog import SettingsDialog


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
