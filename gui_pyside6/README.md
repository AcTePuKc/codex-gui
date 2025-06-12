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

## 📦 Installation

```bash
git clone https://github.com/AcTePuKc/codex-gui
cd codex-gui/gui_pyside6
pip install uv
uv pip install -r requirements.uv.in
./run_pyside6.sh  # Windows: run_pyside6.bat
````

> Requires Python 3.9+ and PySide6

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

## 📚 Docs

For agent presets, architecture decisions, and developer info, see:

* [AGENTS.md](./AGENTS.md)
* [CONTRIBUTING.md](./CONTRIBUTING.md)
* [docs/index.md](./docs/index.md)

## 🔌 Plugins & Backends

Plugins listed in `plugins/manifest.json` are loaded at startup using `load_plugins`. Create a Python module under `plugins/` and enable it in the manifest to extend the UI.

Example plugins included:

- **Syntax Formatter** – adds a *Format* button that runs the Black formatter on the prompt editor.
- **Agent Logger** – records prompts and responses to `agent_log.txt` when enabled.

Some plugins rely on optional TTS backends. These dependencies are installed on demand via `ensure_backend_installed()` which detects your active virtual environment or falls back to `~/.hybrid_tts/venv`.

## 🙏 Credits

Based on [OpenAI Codex](https://github.com/openai/codex)

---
