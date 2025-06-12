from __future__ import annotations


from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLabel,
    QPlainTextEdit,
)

from .settings_dialog import SettingsDialog
from ..backend.settings_manager import save_settings

from ..backend import codex_adapter
from ..backend.agent_manager import AgentManager
from ..plugins.loader import load_plugins


class CodexWorker(QThread):
    """Worker thread to stream Codex output."""

    line_received = Signal(str)
    finished = Signal()

    def __init__(self, prompt: str, agent: dict) -> None:
        super().__init__()
        self.prompt = prompt
        self.agent = agent

    def run(self) -> None:  # type: ignore[override]
        try:
            for line in codex_adapter.start_session(self.prompt, self.agent):
                self.line_received.emit(line)
        except Exception as exc:  # pylint: disable=broad-except
            self.line_received.emit(f"Error: {exc}")
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self, agent_manager: AgentManager, settings: dict) -> None:
        super().__init__()
        self.agent_manager = agent_manager
        self.settings = settings
        self.worker: CodexWorker | None = None

        self.setWindowTitle("Codex-GUI")

        central = QWidget(self)
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        top_bar = QHBoxLayout()
        layout.addLayout(top_bar)

        top_bar.addWidget(QLabel("Agent:"))
        self.agent_combo = QComboBox()
        self.agent_combo.addItems([a.get("name", "") for a in agent_manager.agents])
        index = self.agent_combo.findText(self.settings.get("selected_agent", ""))
        if index >= 0:
            self.agent_combo.setCurrentIndex(index)
        top_bar.addWidget(self.agent_combo)
        self.agent_combo.currentTextChanged.connect(self.on_agent_changed)

        self.settings_btn = QPushButton("Settings")
        top_bar.addWidget(self.settings_btn)
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your prompt here...")
        layout.addWidget(self.prompt_edit)

        button_bar = QHBoxLayout()
        layout.addLayout(button_bar)
        self.button_bar = button_bar

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self.start_codex)
        button_bar.addWidget(self.run_btn)

        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_codex)
        button_bar.addWidget(self.stop_btn)

        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        layout.addWidget(self.output_view)

        # Load optional plugins defined in plugins/manifest.json
        load_plugins(self)

    def start_codex(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        prompt = self.prompt_edit.toPlainText().strip()
        agent_name = self.agent_combo.currentText()
        self.agent_manager.set_active_agent(agent_name)
        agent = self.agent_manager.active_agent or {}

        self.output_view.clear()
        self.worker = CodexWorker(prompt, agent)
        self.worker.line_received.connect(self.append_output)
        self.worker.finished.connect(self.session_finished)
        self.worker.start()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def append_output(self, text: str) -> None:
        self.output_view.append(text)

    def session_finished(self) -> None:
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def stop_codex(self) -> None:
        codex_adapter.stop_session()
        if self.worker and self.worker.isRunning():
            self.worker.wait(1000)
        self.session_finished()

    def on_agent_changed(self, name: str) -> None:
        """Handle selection changes in the agent combo box."""
        self.agent_manager.set_active_agent(name)
        self.settings["selected_agent"] = name
        save_settings(self.settings)

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        dialog.exec()
