# Codex-GUI

A full-featured **PySide6-based GUI** frontend for [OpenAI's Codex CLI](https://github.com/openai/codex).

This project reimagines the Codex CLI as a desktop application, offering:

- User-friendly prompt editor
- Multi-agent support with visual memory
- Plugin-ready architecture
- File-aware completions
- Conversation context tracking
- Toggleable features from CLI (e.g., `--no-browser`, `--dry-run`)

> **Note**: This is an experimental fork developed at [https://github.com/AcTePuKc/codex-gui](https://github.com/AcTePuKc/codex-gui)

## Features (Planned)

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
- Show or hide the left and right panels, or the Debug Console, from the **View** menu

Quiet and full context can be toggled from the **Settings** dialog.
Example snippet:
```python
self.quiet_check = QCheckBox("Quiet Mode")
self.full_context_check = QCheckBox("Full Context")
```
- Additional options for provider, model, top-p, frequency and presence penalties,
  approval mode with auto-edit/full-auto toggles, reasoning effort and flex mode

## Prerequisites

- Python 3.9 or newer
- Node.js **22+** installed and on your `PATH`
- A working **Codex CLI** installation. Verify by running:

```bash
codex --help
```

If the command fails, install the CLI globally using `npm install -g @openai/codex`.

### Package manager detection

The launch scripts automatically choose `pnpm` when it is available and fall back
to `npm` otherwise. On Windows you can see this logic in
`run.bat`:

```bat
where pnpm >nul 2>&1
if %errorlevel%==0 (
    set "PKG_MGR=pnpm"
    echo pnpm found.
) else (
    echo pnpm not found. Checking for npm fallback...
    where npm >nul 2>&1
    if %errorlevel%==0 (
        set "PKG_MGR=npm"
        echo npm found.
        echo   Tip: pnpm is faster. You can install it via: npm install -g pnpm
    )
)
```

If you wish to use `pnpm` globally, run `pnpm setup` (or
`corepack enable && corepack prepare pnpm@latest --activate` on Node.js 22+) so
the command is available on your `PATH`.

## Installation

```bash
git clone https://github.com/AcTePuKc/codex-gui
cd codex-gui/gui_pyside6
./run.sh  # Windows: run.bat
````

> Requires Python 3.9+

Running the script detects an active virtual environment. If none is found, it
creates `~/.hybrid_tts/venv` (Windows: `%USERPROFILE%\.hybrid_tts\venv`) for
the optional text-to-speech backends, installs the requirements using `uv`, and
then launches the GUI in a separate terminal window. This environment persists
for future runs and a `.deps_installed` file prevents reinstalling packages
unless `requirements.uv.in` changes. Delete the `~/.hybrid_tts/venv` directory
to force a fresh setup or edit the `VENV_DIR` variable near the top of
`run.*` if you wish to relocate it.

## First-Time Setup

1. Run `./run.sh` (Windows: `run.bat`).
2. The script installs **Codex CLI** automatically with `npm install -g @openai/codex` if it is not already present.
3. On Windows the installer will retry with `--registry=https://registry.npmmirror.com` if the initial global install fails.
4. If you choose the **OpenAI** provider, the GUI prompts for an API key the first time you run a session or refresh models when `OPENAI_API_KEY` is not set.

To set the key manually for the OpenAI provider:

```bash
export OPENAI_API_KEY="sk-your-key"
# Windows
set OPENAI_API_KEY=sk-your-key
```

## Login & Free Credits

Under the **Help** menu you can run two useful commands (only needed when using the OpenAI provider):

- **Login** - launches `codex --login` and opens a browser window to authenticate
  your OpenAI account.
- **Redeem Free Credits** - runs `codex --free` to claim any promotional credits
  that may be available.

The command output is shown in the main panel and logged in the Debug Console.

## Troubleshooting

### CLI not detected

If running `codex --help` works in a terminal but the GUI reports that it cannot
find **Codex CLI**, open **File -> Settings** and enter the full path to the
`codex` executable (or `codex.cmd` on Windows). When installed with **pnpm** the
binary is usually located under `~/.local/share/pnpm` on Linux/macOS or
`C:\Users\NAME\AppData\Local\pnpm` on Windows. Pointing the setting to this
file ensures the GUI can launch the CLI correctly.

---

## Project Structure

- `codex/` - The CLI backend, written in TypeScript. Run `pnpm run build` only when making CLI changes.
- `gui_pyside6/` - A full-featured Python GUI using PySide6.

These components are developed separately but communicate via a common API/backend.
- `gui_pyside6/main.py` - The main entry point for the GUI application.
- `gui_pyside6/ui/` - Contains the UI components built with PySide6.
---

## Project Structure (WIP)

```
codex-gui/
|-- gui_pyside6/
|   |-- main.py
|   |-- run.sh
|   |-- run.bat
|   |-- ui/                   # UI components
|   |-- backend/              # Logic & CLI adapters
|   |-- utils/                # Helper functions
|-- AGENTS.md
|-- README.md
|-- CONTRIBUTING.md
|-- docs/
|   `-- index.md
```

---

## IDE Layout

The window is split into three panels using a horizontal splitter:

- **Left panel** - shows the list of agents and their description.
- **Center panel** - contains the prompt editor and the streaming output view.
- **Right panel** - displays the conversation history.

A toolbar at the top mirrors the **Run** and **Stop** actions found below the
editor. The status bar reports which agent is active and session progress.
If the Codex CLI encounters an error, its stderr output will appear in the output panel.
Detailed logs from Codex and tool executions are also sent to the dockable **Debug Console** accessible from the **View** menu.

## Debug Console

The console is a dockable pane that captures stdout and stderr from Codex and
any running tools. Toggle it from **View -> Debug Console**. The window offers
**Info** and **Errors** checkboxes to filter messages and a **Clear** button to
reset the log.

## Docs

For agent presets, architecture decisions, and developer info, see:

* [AGENTS.md](./AGENTS.md)
* [CONTRIBUTING.md](./CONTRIBUTING.md)
* [docs/index.md](./docs/index.md)

## Plugins & Backends

Plugins listed in `plugins/manifest.json` are loaded at startup using `load_plugins`.
Place your plugin module inside `gui_pyside6/plugins/` and enable it in the manifest to extend the UI.
Each module simply exposes a `register(window)` function that receives the main window instance.

Example plugins included:

- **Syntax Formatter** - adds a *Format* button that runs the Black formatter on the prompt editor.
- **Agent Logger** - records prompts and responses to `agent_log.txt` when enabled.
- **TTS Player** - speaks the current prompt using gTTS (disabled by default).

Some plugins rely on optional TTS backends. These dependencies are installed on demand via `ensure_backend_installed()` which detects your active virtual environment or falls back to `~/.hybrid_tts/venv`.

## Plugin Manager

Use **Plugins -> Plugin Manager** to enable or disable optional plugins from the
GUI. The dialog lists each entry from `plugins/manifest.json` with a checkbox.
Click **Save** to persist your selection and reload the plugins immediately.

## FAQ

### Why was `~/.hybrid_tts/venv` created?

When the launcher script doesn't find an active Python virtual environment, it
initializes one at `~/.hybrid_tts/venv` (or `%USERPROFILE%\.hybrid_tts\venv` on
Windows) for the optional text-to-speech backends. The folder is reused on every
launch. Remove it if you want to reclaim space or force a reinstall.

## Credits

Based on [OpenAI Codex](https://github.com/openai/codex)

---
