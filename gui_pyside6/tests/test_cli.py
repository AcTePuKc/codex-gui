import os
import pytest
try:
    from PySide6.QtWidgets import QApplication
except Exception as exc:  # pylint: disable=broad-except
    pytest.skip(f"PySide6 not available: {exc}", allow_module_level=True)

from gui_pyside6.backend import codex_adapter
from gui_pyside6.backend.agent_manager import AgentManager
from gui_pyside6.ui import main_window as main_window_module


def test_build_command_returns_list_of_str():
    agent = {"temperature": 0.3, "model": "gpt"}
    settings = {"cli_path": "codex"}
    cmd = codex_adapter.build_command("hello", agent, settings)
    assert isinstance(cmd, list)
    assert all(isinstance(part, str) for part in cmd)


def test_build_command_with_npx_command():
    agent = {"temperature": 0.3}
    settings = {"cli_path": "npx codex --no-update-notifier"}
    cmd = codex_adapter.build_command("hi", agent, settings)
    assert cmd[:3] == ["npx", "codex", "--no-update-notifier"]
    assert cmd[-1] == "hi"


def test_start_codex_handles_command(monkeypatch):
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])

    # prevent actual CLI checks and execution
    monkeypatch.setattr(codex_adapter, "ensure_cli_available", lambda *a, **k: None)
    monkeypatch.setattr(codex_adapter, "start_session", lambda *a, **k: iter([]))

    class DummySignal:
        def connect(self, fn):
            pass

    class DummyWorker:
        def __init__(self, *a, **k):
            self.line_received = DummySignal()
            self.log_line = DummySignal()
            self.finished = DummySignal()
        def start(self):
            pass
        def isRunning(self):
            return False

    monkeypatch.setattr(main_window_module, "CodexWorker", DummyWorker)

    agent_manager = AgentManager()
    settings = {}
    window = main_window_module.MainWindow(agent_manager, settings)
    window.prompt_edit.setPlainText("hi")
    window.start_codex()

