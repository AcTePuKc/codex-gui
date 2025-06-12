from __future__ import annotations


from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import (
    QAction,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QToolBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QMessageBox,
    QSplitter,
    QListWidget,
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

        # ----------------------- Menu Bar -----------------------
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        settings_menu = menu_bar.addMenu("Settings")
        help_menu = menu_bar.addMenu("Help")
        history_menu = menu_bar.addMenu("History")

        self.run_action = QAction("Run", self)
        self.run_action.triggered.connect(self.start_codex)
        file_menu.addAction(self.run_action)

        self.stop_action = QAction("Stop", self)
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self.stop_codex)
        file_menu.addAction(self.stop_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(settings_action)

        about_action = QAction("About", self)
        help_menu.addAction(about_action)
        about_action.triggered.connect(
            lambda: QMessageBox.about(self, "About Codex-GUI", "Codex-GUI")
        )

        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self.clear_history)
        history_menu.addAction(clear_history_action)

        # ----------------------- Toolbar -----------------------
        toolbar = QToolBar("Main", self)
        self.addToolBar(toolbar)
        toolbar.addAction(self.run_action)
        toolbar.addAction(self.stop_action)

        # Instantiate status bar
        self.status_bar = self.statusBar()

        splitter = QSplitter(Qt.Horizontal, self)
        self.setCentralWidget(splitter)

        # ----------------------- Left Panel -----------------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        self.agent_list = QListWidget()
        self.agent_list.addItems([a.get("name", "") for a in agent_manager.agents])
        current_name = self.settings.get("selected_agent", "")
        matches = self.agent_list.findItems(current_name, Qt.MatchExactly)
        if matches:
            item = matches[0]
            self.agent_list.setCurrentItem(item)
            self.agent_manager.set_active_agent(item.text())
        elif self.agent_list.count() > 0:
            self.agent_list.setCurrentRow(0)
            self.agent_manager.set_active_agent(self.agent_list.currentItem().text())
        self.agent_list.currentTextChanged.connect(self.on_agent_changed)
        left_layout.addWidget(self.agent_list)

        # Show description and status for the initially selected agent
        self.update_agent_description()
        if self.agent_list.currentItem():
            self.status_bar.showMessage(
                f"Active Agent: {self.agent_list.currentItem().text()}"
            )

        self.agent_desc = QPlainTextEdit()
        self.agent_desc.setReadOnly(True)
        left_layout.addWidget(self.agent_desc)

        splitter.addWidget(left_panel)

        # ----------------------- Center Panel -----------------------
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)

        top_bar = QHBoxLayout()
        center_layout.addLayout(top_bar)

        self.settings_btn = QPushButton("Settings")
        top_bar.addWidget(self.settings_btn)
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your prompt here...")
        center_layout.addWidget(self.prompt_edit)

        button_bar = QHBoxLayout()
        center_layout.addLayout(button_bar)
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
        center_layout.addWidget(self.output_view)

        splitter.addWidget(center_widget)

        # ----------------------- Right Panel -----------------------
        self.history_view = QPlainTextEdit()
        self.history_view.setReadOnly(True)
        splitter.addWidget(self.history_view)

        splitter.setStretchFactor(1, 1)

        # Load optional plugins defined in plugins/manifest.json
        load_plugins(self)

    def start_codex(self) -> None:
        if self.worker and self.worker.isRunning():
            return
        prompt = self.prompt_edit.toPlainText().strip()
        agent_item = self.agent_list.currentItem()
        agent_name = agent_item.text() if agent_item else ""
        self.agent_manager.set_active_agent(agent_name)
        agent = self.agent_manager.active_agent or {}

        self.output_view.clear()
        self.worker = CodexWorker(prompt, agent)
        self.worker.line_received.connect(self.append_output)
        self.worker.finished.connect(self.session_finished)
        self.worker.start()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.run_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        self.status_bar.showMessage("Running Codex session...")

    def append_output(self, text: str) -> None:
        self.output_view.append(text)
        self.history_view.appendPlainText(text)

    def session_finished(self) -> None:
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.run_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.status_bar.showMessage("Session finished")

    def stop_codex(self) -> None:
        codex_adapter.stop_session()
        if self.worker and self.worker.isRunning():
            self.worker.wait(1000)
        self.session_finished()

    def on_agent_changed(self, name: str) -> None:
        """Handle selection changes in the agent list."""
        self.agent_manager.set_active_agent(name)
        self.settings["selected_agent"] = name
        save_settings(self.settings)
        self.status_bar.showMessage(f"Active Agent: {name}")
        self.update_agent_description()
        
    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        dialog.exec()
        self.status_bar.showMessage("Settings updated")

    def clear_history(self) -> None:
        """Clear the history panel."""
        self.history_view.clear()

    def update_agent_description(self) -> None:
        """Update the description panel with the active agent's details."""
        agent = self.agent_manager.active_agent
        if agent:
            self.agent_desc.setPlainText(agent.get("description", ""))
        else:
            self.agent_desc.clear()
