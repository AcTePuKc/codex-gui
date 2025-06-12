from __future__ import annotations


from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import (
    QFontDatabase,
    QAction,
    QTextCharFormat,
    QColor,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QToolBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QMessageBox,
    QSplitter,
    QListWidget,
    QFileDialog,
    QLabel,
)

from .settings_dialog import SettingsDialog
from .tools_panel import ToolsPanel
from ..backend.settings_manager import save_settings

from ..backend import codex_adapter
from ..backend.agent_manager import AgentManager
from ..plugins.loader import load_plugins
from ..utils.highlighter import PythonHighlighter
from pathlib import Path


class ImageDropList(QListWidget):
    """List widget that accepts image file drops."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if path:
                    self.addItem(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class CodexWorker(QThread):
    """Worker thread to stream Codex output."""

    line_received = Signal(str)
    finished = Signal()

    def __init__(
        self,
        prompt: str,
        agent: dict,
        settings: dict,
        view_path: str | None = None,
        images: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.prompt = prompt
        self.agent = agent
        self.settings = settings
        self.view_path = view_path
        self.images = images or []

    def run(self) -> None:  # type: ignore[override]
        try:
            for line in codex_adapter.start_session(
                self.prompt,
                self.agent,
                self.settings,
                view=self.view_path,
                images=self.images,
            ):
                self.line_received.emit(line)
        except codex_adapter.CodexError as exc:
            for err_line in exc.stderr.strip().splitlines():
                self.line_received.emit(f"Error: {err_line}")
            self.line_received.emit(f"Error: {exc}")
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

        browse_action = QAction("Browse Sessions", self)
        browse_action.triggered.connect(self.open_sessions_dialog)
        history_menu.addAction(browse_action)

        view_action = QAction("View Rollout...", self)
        view_action.triggered.connect(self.select_rollout_file)
        history_menu.addAction(view_action)

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

        self.agent_desc = QPlainTextEdit()
        self.agent_desc.setReadOnly(True)
        left_layout.addWidget(self.agent_desc)

        # Show description and status for the initially selected agent
        self.update_agent_description()
        if self.agent_list.currentItem():
            self.status_bar.showMessage(
                f"Active Agent: {self.agent_list.currentItem().text()}"
            )

        splitter.addWidget(left_panel)

        # ----------------------- Center Panel -----------------------
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)

        top_bar = QHBoxLayout()
        center_layout.addLayout(top_bar)

        self.settings_btn = QPushButton("Settings")
        top_bar.addWidget(self.settings_btn)
        self.settings_btn.clicked.connect(self.open_settings_dialog)

        self.tools_btn = QPushButton("Tools")
        top_bar.addWidget(self.tools_btn)
        self.tools_btn.clicked.connect(self.open_tools_panel)

        images_row = QHBoxLayout()
        center_layout.addLayout(images_row)
        images_row.addWidget(QLabel("Images:"))
        self.image_list = ImageDropList()
        self.image_list.setMaximumHeight(60)
        images_row.addWidget(self.image_list)
        self.add_image_btn = QPushButton("Add Image")
        self.add_image_btn.clicked.connect(self.browse_images)
        images_row.addWidget(self.add_image_btn)
        self.remove_image_btn = QPushButton("Remove")
        self.remove_image_btn.clicked.connect(self.remove_selected_images)
        images_row.addWidget(self.remove_image_btn)

        inner_splitter = QSplitter(Qt.Vertical)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setPlaceholderText("Enter your prompt here...")
        inner_splitter.addWidget(self.prompt_edit)

        self.output_view = QPlainTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setFont(QFontDatabase.systemFont(QFontDatabase.FixedFont))
        inner_splitter.addWidget(self.output_view)

        inner_splitter.setStretchFactor(0, 1)
        inner_splitter.setStretchFactor(1, 2)
        center_layout.addWidget(inner_splitter)

        self.highlighter = PythonHighlighter(self.output_view.document())

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

        splitter.addWidget(center_widget)

        # ----------------------- Right Panel -----------------------
        self.history_view = QPlainTextEdit()
        self.history_view.setReadOnly(True)
        splitter.addWidget(self.history_view)

        splitter.setStretchFactor(1, 1)

        # Load optional plugins defined in plugins/manifest.json
        load_plugins(self)

    def start_codex(
        self, prompt: str | None = None, view_path: str | None = None
    ) -> None:
        if self.worker and self.worker.isRunning():
            return
        try:
            codex_adapter.ensure_cli_available(self.settings)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "Codex CLI Missing", str(exc))
            self.status_bar.showMessage(str(exc))
            return
        prompt_text = (
            prompt if prompt is not None else self.prompt_edit.toPlainText().strip()
        )
        agent_item = self.agent_list.currentItem()
        agent_name = agent_item.text() if agent_item else ""
        self.agent_manager.set_active_agent(agent_name)
        self.settings["selected_agent"] = agent_name
        save_settings(self.settings)
        agent = self.agent_manager.active_agent or {}

        self.output_view.clear()
        image_paths = [
            self.image_list.item(i).text() for i in range(self.image_list.count())
        ]
        cmd = codex_adapter.build_command(
            prompt_text,
            agent,
            self.settings,
            view=view_path,
            images=image_paths if image_paths else None,
        )
        if self.settings.get("verbose"):
            self.append_output("$ " + " ".join(cmd))
        self.worker = CodexWorker(
            prompt_text,
            agent,
            self.settings,
            view_path,
            images=image_paths,
        )
        self.worker.line_received.connect(self.append_output)
        self.worker.finished.connect(self.session_finished)
        self.worker.start()
        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.run_action.setEnabled(False)
        self.stop_action.setEnabled(True)
        msg = "Running Codex session"
        modes: list[str] = []
        if self.settings.get("quiet"):
            modes.append("quiet")
        if self.settings.get("full_context"):
            modes.append("full context")
        if modes:
            msg += " (" + ", ".join(modes) + ")"
        msg += "..."
        self.status_bar.showMessage(msg)

    def append_output(self, text: str) -> None:
        cursor = self.output_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        if text.startswith("Error:"):
            fmt.setForeground(QColor("red"))
        cursor.insertText(text + "\n", fmt)
        self.output_view.setTextCursor(cursor)
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

    def open_tools_panel(self) -> None:
        dialog = ToolsPanel(self)
        dialog.exec()

    def clear_history(self) -> None:
        """Clear the history panel."""
        self.history_view.clear()

    def browse_images(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select image files",
            str(Path.home()),
            "Image Files (*.png *.jpg *.jpeg *.gif *.bmp)",
        )
        for path in files:
            if not any(
                path == self.image_list.item(i).text()
                for i in range(self.image_list.count())
            ):
                self.image_list.addItem(path)

    def remove_selected_images(self) -> None:
        for item in self.image_list.selectedItems():
            self.image_list.takeItem(self.image_list.row(item))

    def update_agent_description(self) -> None:
        """Update the description panel with the active agent's details."""
        agent = self.agent_manager.active_agent
        if agent:
            self.agent_desc.setPlainText(agent.get("description", ""))
        else:
            self.agent_desc.clear()

    # ------------------------------------------------------------------
    # Session history helpers
    # ------------------------------------------------------------------

    def open_sessions_dialog(self) -> None:
        from .sessions_dialog import SessionsDialog
        from ..utils.sessions import load_sessions

        sessions = load_sessions()
        if not sessions:
            QMessageBox.information(self, "No Sessions", "No previous sessions found.")
            return

        dialog = SessionsDialog(sessions, self)
        if dialog.exec() and dialog.selected_path:
            if dialog.mode == "view":
                self.view_rollout(dialog.selected_path)
            elif dialog.mode == "resume":
                self.resume_session(dialog.selected_path)

    def view_rollout(self, path: str) -> None:
        self.start_codex("", view_path=path)

    def resume_session(self, path: str) -> None:
        self.start_codex(f"Resume this session: {path}")

    def select_rollout_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select rollout file",
            str(Path.home() / ".codex" / "sessions"),
            "JSON Files (*.json)",
        )
        if filename:
            self.view_rollout(filename)
