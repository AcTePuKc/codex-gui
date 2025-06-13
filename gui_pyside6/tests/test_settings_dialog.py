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
