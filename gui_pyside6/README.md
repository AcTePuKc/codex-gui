# Codex-GUI

A full-featured **PySide6-based GUI** frontend for [OpenAI's Codex CLI](https://github.com/openai/codex).

This project reimagines the Codex CLI as a desktop application, offering:

- 🖥️ User-friendly prompt editor
- 🧠 Multi-agent support with visual memory
- 🧩 Plugin-ready architecture
- 📁 File-aware completions
- 💬 Conversation context tracking
- 🔌 Toggleable features from CLI (e.g., `--no-browser`, `--dry-run`)

> ⚠️ This is an experimental fork developed at [https://github.com/AcTePuKc/codex-gui](https://github.com/AcTePuKc/codex-gui)

## 🚀 Features (Planned)

- Full CLI parity with real-time feedback
- Drag-and-drop file support
- Tabs for conversations / prompts
- Agent presets with editable configs
- Live preview of completions
- Export/import conversations
- Runtime settings for temperature, model, provider, penalties and more passed as CLI flags
- Remembers the last selected agent across restarts
- Optional verbose mode prints the exact CLI command before execution
- Quiet mode hides progress output while Full Context sends the entire conversation. Both map to the CLI flags `--quiet` and `--full-context`
- Dockable **Debug Console** shows stdout/stderr from Codex and tool runs

Quiet and full context can be toggled from the **Settings** dialog.
Example snippet:
```python
self.quiet_check = QCheckBox("Quiet Mode")
self.full_context_check = QCheckBox("Full Context")
```
- Additional options for provider, model, top-p, frequency and presence penalties,
  approval mode with auto-edit/full-auto toggles, reasoning effort and flex mode

## 📝 Prerequisites

- Python 3.9 or newer
- A built copy of **Codex CLI**. From the `codex-cli` directory run:

```bash
node bin/codex.js --help
```

If the command fails, install dependencies and build the CLI using `pnpm install && pnpm build`.

## 📦 Installation

```bash
git clone https://github.com/AcTePuKc/codex-gui
cd codex-gui/gui_pyside6
./run_pyside6.sh  # Windows: run_pyside6.bat
````

> Requires Python 3.9+

Running the script detects an active virtual environment. If none is found, it
creates `~/.hybrid_tts/venv` (Windows: `%USERPROFILE%\.hybrid_tts\venv`) for
the optional text-to-speech backends, installs the requirements using `uv`, and
then launches the GUI in a separate terminal window.

## 🔧 Project Structure (WIP)

```
codex-gui/
├── gui_pyside6/
│   ├── main.py
│   ├── run_pyside6.sh
│   ├── run_pyside6.bat
│   ├── ui/                   # UI components
│   ├── backend/              # Logic & CLI adapters
│   ├── utils/                # Helper functions
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── docs/
│   └── index.md
```

## 🗺️ IDE Layout

The window is split into three panels using a horizontal splitter:

- **Left panel** – shows the list of agents and their description.
- **Center panel** – contains the prompt editor and the streaming output view.
- **Right panel** – displays the conversation history.

A toolbar at the top mirrors the **Run** and **Stop** actions found below the
editor. The status bar reports which agent is active and session progress.
If the Codex CLI encounters an error, its stderr output will appear in the output panel.
Detailed logs from Codex and tool executions are also sent to the dockable **Debug Console** accessible from the **View** menu.

## 📚 Docs

For agent presets, architecture decisions, and developer info, see:

* [AGENTS.md](./AGENTS.md)
* [CONTRIBUTING.md](./CONTRIBUTING.md)
* [docs/index.md](./docs/index.md)

## 🔌 Plugins & Backends

Plugins listed in `plugins/manifest.json` are loaded at startup using `load_plugins`.
Place your plugin module inside `gui_pyside6/plugins/` and enable it in the manifest to extend the UI.
Each module simply exposes a `register(window)` function that receives the main window instance.

Example plugins included:

- **Syntax Formatter** – adds a *Format* button that runs the Black formatter on the prompt editor.
- **Agent Logger** – records prompts and responses to `agent_log.txt` when enabled.
- **TTS Player** – speaks the current prompt using gTTS (disabled by default).

Some plugins rely on optional TTS backends. These dependencies are installed on demand via `ensure_backend_installed()` which detects your active virtual environment or falls back to `~/.hybrid_tts/venv`.

## ❓ FAQ

### Why was `~/.hybrid_tts/venv` created?

When the launcher script doesn't find an active Python virtual environment, it
initializes one at `~/.hybrid_tts/venv` (or `%USERPROFILE%\.hybrid_tts\venv` on
Windows) for the optional text-to-speech backends. If you don't plan to use any
TTS features, you can safely remove this directory.

## 🙏 Credits

Based on [OpenAI Codex](https://github.com/openai/codex)

---
