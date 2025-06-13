from __future__ import annotations


from PySide6.QtCore import QThread, Signal, Qt, QStringListModel
from PySide6.QtGui import (
    QFontDatabase,
    QAction,
    QTextCharFormat,
    QColor,
    QTextCursor,
    QKeySequence,
    QShortcut,
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
    QCompleter,
    QMessageBox,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QInputDialog,
    QFileDialog,
    QLabel,
)

from .settings_dialog import SettingsDialog
from .tools_panel import ToolsPanel
from .debug_console import DebugConsole
from .agent_editor_dialog import AgentEditorDialog, AgentJsonDialog
from ..backend.settings_manager import save_settings

from ..backend import codex_adapter
from ..backend.agent_manager import AgentManager
from ..plugins.loader import load_plugins
from ..utils.highlighter import PythonHighlighter
from ..utils.file_scanner import find_source_files
from ..utils.project_paths import get_common_paths
from ..utils.api_key import ensure_api_key
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


class PromptEdit(QPlainTextEdit):
    """Text edit that can trigger path completion."""

    pathCompletionRequested = Signal()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key_Space and event.modifiers() == Qt.ControlModifier:
            self.pathCompletionRequested.emit()
            return
        super().keyPressEvent(event)
        cursor = self.textCursor()
        text = self.toPlainText()[: cursor.position()]
        if text.endswith("--file") or text.endswith("--file "):
            self.pathCompletionRequested.emit()


class CodexWorker(QThread):
    """Worker thread to stream Codex output."""

    line_received = Signal(str)
    log_line = Signal(str, str)  # level, text
    finished = Signal()

    def __init__(
        self,
        prompt: str,
        agent: dict,
        settings: dict,
        view_path: str | None = None,
        images: list[str] | None = None,
        files: list[str] | None = None,
    ) -> None:
        super().__init__()
        self.prompt = prompt
        self.agent = agent
        self.settings = settings
        self.view_path = view_path
        self.images = images or []
        self.files = files or []

    def run(self) -> None:  # type: ignore[override]
        try:
            for line in codex_adapter.start_session(
                self.prompt,
                self.agent,
                self.settings,
                view=self.view_path,
                images=self.images,
                files=self.files,
            ):
                self.line_received.emit(line)
                self.log_line.emit("info", line)
        except codex_adapter.CodexError as exc:
            for err_line in exc.stderr.strip().splitlines():
                self.line_received.emit(f"Error: {err_line}")
                self.log_line.emit("error", err_line)
            self.line_received.emit(f"Error: {exc}")
            self.log_line.emit("error", str(exc))
        except Exception as exc:  # pylint: disable=broad-except
            self.line_received.emit(f"Error: {exc}")
            self.log_line.emit("error", str(exc))
        finally:
            self.finished.emit()


class CodexCommandWorker(QThread):
    """Worker thread for simple Codex CLI commands."""

    line_received = Signal(str)
    log_line = Signal(str, str)
    finished = Signal()

    def __init__(self, run_fn) -> None:
        super().__init__()
        self.run_fn = run_fn

    def run(self) -> None:  # type: ignore[override]
        try:
            for line in self.run_fn():
                self.line_received.emit(line)
                self.log_line.emit("info", line)
        except codex_adapter.CodexError as exc:
            for err_line in exc.stderr.strip().splitlines():
                self.line_received.emit(f"Error: {err_line}")
                self.log_line.emit("error", err_line)
            self.line_received.emit(f"Error: {exc}")
            self.log_line.emit("error", str(exc))
        except Exception as exc:  # pylint: disable=broad-except
            self.line_received.emit(f"Error: {exc}")
            self.log_line.emit("error", str(exc))
        finally:
            self.finished.emit()


class MainWindow(QMainWindow):
    """Primary application window."""

    def __init__(self, agent_manager: AgentManager, settings: dict) -> None:
        super().__init__()
        self.agent_manager = agent_manager
        self.settings = settings
        self.worker: QThread | None = None

        self.setWindowTitle("Codex-GUI")

        # ----------------------- Menu Bar -----------------------
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("File")
        settings_menu = menu_bar.addMenu("Settings")
        plugins_menu = menu_bar.addMenu("Plugins")
        agents_menu = menu_bar.addMenu("Agents")
        history_menu = menu_bar.addMenu("History")
        view_menu = menu_bar.addMenu("View")
        help_menu = menu_bar.addMenu("Help")

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

        plugin_mgr_action = QAction("Plugin Manager", self)
        plugin_mgr_action.triggered.connect(self.open_plugin_manager)
        plugins_menu.addAction(plugin_mgr_action)

        new_agent_action = QAction("New Agent", self)
        new_agent_action.triggered.connect(self.create_agent)
        edit_agent_action = QAction("Edit Agent", self)
        edit_agent_action.triggered.connect(self.edit_agent)
        edit_json_action = QAction("Edit Agent JSON", self)
        edit_json_action.triggered.connect(self.edit_agent_json)
        agents_menu.addAction(new_agent_action)
        agents_menu.addAction(edit_agent_action)
        agents_menu.addAction(edit_json_action)

        about_action = QAction("About", self)
        help_menu.addAction(about_action)
        about_action.triggered.connect(
            lambda: QMessageBox.about(self, "About Codex-GUI", "Codex-GUI")
        )

        self.login_action = QAction("Login", self)
        self.login_action.triggered.connect(self.run_login)
        help_menu.addAction(self.login_action)

        self.free_action = QAction("Redeem Free Credits", self)
        self.free_action.triggered.connect(self.redeem_free_credits)
        help_menu.addAction(self.free_action)

        self.debug_console = DebugConsole(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.debug_console)

        toggle_console_action = QAction("Debug Console", self)
        toggle_console_action.setCheckable(True)
        toggle_console_action.setChecked(True)
        toggle_console_action.toggled.connect(self.debug_console.setVisible)
        self.debug_console.visibilityChanged.connect(toggle_console_action.setChecked)
        view_menu.addAction(toggle_console_action)

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
        self.left_panel = QWidget()
        left_layout = QVBoxLayout(self.left_panel)

        self.agent_list = QListWidget()
        for a in agent_manager.agents:
            item = QListWidgetItem(a.get("name", ""))
            item.setToolTip(a.get("description", ""))
            self.agent_list.addItem(item)
        self.agent_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.agent_list.customContextMenuRequested.connect(self.show_agent_menu)
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

        splitter.addWidget(self.left_panel)

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

        files_row = QHBoxLayout()
        center_layout.addLayout(files_row)
        files_row.addWidget(QLabel("Files:"))
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(60)
        files_row.addWidget(self.file_list)
        self.add_file_btn = QPushButton("Add File")
        self.add_file_btn.clicked.connect(self.browse_files)
        files_row.addWidget(self.add_file_btn)
        self.remove_file_btn = QPushButton("Remove")
        self.remove_file_btn.clicked.connect(self.remove_selected_files)
        files_row.addWidget(self.remove_file_btn)

        inner_splitter = QSplitter(Qt.Vertical)

        self.prompt_edit = PromptEdit()
        self.prompt_edit.setPlaceholderText("Enter your prompt here...")
        inner_splitter.addWidget(self.prompt_edit)

        self.path_completer = QCompleter()
        self.path_completer.setModel(QStringListModel())
        self.path_completer.setWidget(self.prompt_edit)
        self.path_completer.activated.connect(self.insert_completion)
        self.prompt_edit.pathCompletionRequested.connect(self.show_path_completion)
        QShortcut(
            QKeySequence(Qt.CTRL | Qt.Key_Space), self.prompt_edit
        ).activated.connect(self.show_path_completion)

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

        toggle_left_panel_action = QAction("Left Panel", self)
        toggle_left_panel_action.setCheckable(True)
        toggle_left_panel_action.setChecked(True)
        toggle_left_panel_action.toggled.connect(self.left_panel.setVisible)
        view_menu.addAction(toggle_left_panel_action)

        toggle_right_panel_action = QAction("Right Panel", self)
        toggle_right_panel_action.setCheckable(True)
        toggle_right_panel_action.setChecked(True)
        toggle_right_panel_action.toggled.connect(self.history_view.setVisible)
        view_menu.addAction(toggle_right_panel_action)

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
            self.debug_console.append_error(str(exc))
            return
        provider = self.settings.get("provider", "openai")
        if provider not in {"local", "custom"}:
            if not ensure_api_key(provider, self):
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
        if self.file_list.count() == 0:
            for path in self.suggest_source_files():
                self.file_list.addItem(path)
        file_paths = [
            self.file_list.item(i).text() for i in range(self.file_list.count())
        ]
        cmd = codex_adapter.build_command(
            prompt_text,
            agent,
            self.settings,
            view=view_path,
            images=image_paths if image_paths else None,
            files=file_paths if file_paths else None,
        )
        if self.settings.get("verbose"):
            self.append_output("$ " + " ".join(cmd))
        self.debug_console.append_info("$ " + " ".join(cmd))
        self.worker = CodexWorker(
            prompt_text,
            agent,
            self.settings,
            view_path,
            images=image_paths,
            files=file_paths,
        )
        self.worker.line_received.connect(self.append_output)
        self.worker.log_line.connect(self.handle_log_line)
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

    def handle_log_line(self, level: str, text: str) -> None:
        if level == "error":
            self.debug_console.append_error(text)
        else:
            self.debug_console.append_info(text)

    def session_finished(self) -> None:
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.run_action.setEnabled(True)
        self.stop_action.setEnabled(False)
        self.status_bar.showMessage("Session finished")
        self.debug_console.append_info("Session finished")

    def stop_codex(self) -> None:
        codex_adapter.stop_session()
        if self.worker and self.worker.isRunning():
            self.worker.wait(1000)
        self.session_finished()
        self.debug_console.append_info("Codex session stopped")

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
        dialog = ToolsPanel(self, debug_console=self.debug_console)
        dialog.exec()

    def open_plugin_manager(self) -> None:
        from .plugin_manager_dialog import PluginManagerDialog

        dialog = PluginManagerDialog(self)
        if dialog.exec():
            load_plugins(self)

    def clear_history(self) -> None:
        """Clear the history panel."""
        self.history_view.clear()

    def refresh_agent_list(self) -> None:
        self.agent_list.clear()
        for agent in self.agent_manager.agents:
            item = QListWidgetItem(agent.get("name", ""))
            item.setToolTip(agent.get("description", ""))
            self.agent_list.addItem(item)

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

    def browse_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files",
            str(Path.cwd()),
            "All Files (*)",
        )
        for path in files:
            if not any(
                path == self.file_list.item(i).text()
                for i in range(self.file_list.count())
            ):
                self.file_list.addItem(path)

    def remove_selected_images(self) -> None:
        for item in self.image_list.selectedItems():
            self.image_list.takeItem(self.image_list.row(item))

    def remove_selected_files(self) -> None:
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def suggest_source_files(self) -> list[str]:
        """Return a list of source files discovered in the current directory."""
        return find_source_files(Path.cwd(), max_files=20)

    def show_path_completion(self) -> None:
        """Display a popup with common file paths for completion."""
        paths = get_common_paths(Path.cwd(), max_files=100)
        model = self.path_completer.model()
        if isinstance(model, QStringListModel):
            model.setStringList(paths)
        cursor_rect = self.prompt_edit.cursorRect()
        self.path_completer.complete(cursor_rect)

    def insert_completion(self, text: str) -> None:
        cursor = self.prompt_edit.textCursor()
        cursor.insertText(text)
        self.prompt_edit.setTextCursor(cursor)

    def update_agent_description(self) -> None:
        """Update the description panel with the active agent's details."""
        agent = self.agent_manager.active_agent
        if agent:
            self.agent_desc.setPlainText(agent.get("description", ""))
        else:
            self.agent_desc.clear()

    def create_agent(self) -> None:
        dialog = AgentEditorDialog(parent=self)
        if dialog.exec():
            self.agent_manager.reload()
            self.refresh_agent_list()
            name = dialog.name_edit.text().strip()
            items = self.agent_list.findItems(name, Qt.MatchExactly)
            if items:
                self.agent_list.setCurrentItem(items[0])
            self.update_agent_description()

    def edit_agent(self) -> None:
        agent = self.agent_manager.active_agent
        if not agent:
            QMessageBox.information(self, "No Agent", "Please select an agent to edit.")
            return
        dialog = AgentEditorDialog(agent, self)
        if dialog.exec():
            self.agent_manager.reload()
            self.refresh_agent_list()
            items = self.agent_list.findItems(agent.get("name", ""), Qt.MatchExactly)
            if items:
                self.agent_list.setCurrentItem(items[0])
            self.update_agent_description()

    def edit_agent_json(self) -> None:
        agent = self.agent_manager.active_agent
        if not agent:
            QMessageBox.information(self, "No Agent", "Please select an agent to edit.")
            return
        dialog = AgentJsonDialog(agent, parent=self)
        if dialog.exec() and dialog.modified:
            self.agent_manager.reload()
            self.refresh_agent_list()
            items = self.agent_list.findItems(agent.get("name", ""), Qt.MatchExactly)
            if items:
                self.agent_list.setCurrentItem(items[0])
            self.update_agent_description()

    def show_agent_menu(self, pos) -> None:
        item = self.agent_list.itemAt(pos)
        if not item:
            return
        self.agent_list.setCurrentItem(item)
        agent = self.agent_manager.active_agent
        menu = QMenu(self)
        edit_act = menu.addAction("Edit")
        json_act = menu.addAction("Edit JSON")
        rename_act = menu.addAction("Rename")
        delete_act = menu.addAction("Delete")
        if agent and self.agent_manager.is_default(agent):
            rename_act.setEnabled(False)
            delete_act.setEnabled(False)
        action = menu.exec(self.agent_list.mapToGlobal(pos))
        if action == edit_act:
            self.edit_agent()
        elif action == json_act:
            self.edit_agent_json()
        elif action == rename_act:
            self.rename_agent()
        elif action == delete_act:
            self.delete_agent()

    def rename_agent(self) -> None:
        agent = self.agent_manager.active_agent
        if not agent:
            return
        if self.agent_manager.is_default(agent):
            QMessageBox.information(self, "Default Agent", "Default presets cannot be renamed.")
            return
        new_name, ok = QInputDialog.getText(self, "Rename Agent", "New name:", text=agent.get("name", ""))
        if not ok or not new_name:
            return
        new_path = Path(agent.get("_path", "")).with_name(new_name.lower().replace(" ", "_") + ".json")
        try:
            self.agent_manager.rename_agent(agent, new_path)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "Rename Failed", str(exc))
            return
        self.agent_manager.reload()
        self.refresh_agent_list()
        items = self.agent_list.findItems(new_name, Qt.MatchExactly)
        if items:
            self.agent_list.setCurrentItem(items[0])
        self.update_agent_description()

    def delete_agent(self) -> None:
        agent = self.agent_manager.active_agent
        if not agent:
            return
        if self.agent_manager.is_default(agent):
            QMessageBox.information(self, "Default Agent", "Default presets cannot be deleted.")
            return
        if QMessageBox.question(
            self,
            "Delete Agent",
            f"Delete '{agent.get('name', '')}'?",
        ) != QMessageBox.Yes:
            return
        try:
            self.agent_manager.delete_agent(agent)
        except Exception as exc:  # pylint: disable=broad-except
            QMessageBox.warning(self, "Delete Failed", str(exc))
            return
        self.refresh_agent_list()
        if self.agent_list.count() > 0:
            self.agent_list.setCurrentRow(0)
            self.on_agent_changed(self.agent_list.currentItem().text())

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

    # ------------------------------------------------------------------
    # CLI helper commands
    # ------------------------------------------------------------------

    def run_login(self) -> None:
        self._run_cli_command(
            lambda: codex_adapter.login(self.settings), "Login finished"
        )

    def redeem_free_credits(self) -> None:
        self._run_cli_command(
            lambda: codex_adapter.redeem_free_credits(self.settings),
            "Credit redemption finished",
        )

    def _run_cli_command(self, fn, done_msg: str) -> None:
        if self.worker and self.worker.isRunning():
            return
        try:
            codex_adapter.ensure_cli_available(self.settings)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "Codex CLI Missing", str(exc))
            self.status_bar.showMessage(str(exc))
            self.debug_console.append_error(str(exc))
            return
        self.output_view.clear()
        self.worker = CodexCommandWorker(fn)
        self.worker.line_received.connect(self.append_output)
        self.worker.log_line.connect(self.handle_log_line)
        self.worker.finished.connect(lambda: self._command_finished(done_msg))
        self.run_btn.setEnabled(False)
        self.run_action.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.stop_action.setEnabled(False)
        self.login_action.setEnabled(False)
        self.free_action.setEnabled(False)
        self.status_bar.showMessage("Running command...")
        self.worker.start()

    def _command_finished(self, msg: str) -> None:
        self.run_btn.setEnabled(True)
        self.run_action.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stop_action.setEnabled(False)
        self.login_action.setEnabled(True)
        self.free_action.setEnabled(True)
        self.status_bar.showMessage(msg)
        self.debug_console.append_info(msg)
