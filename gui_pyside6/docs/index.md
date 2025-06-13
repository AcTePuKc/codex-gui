## `docs/index.md` - Full Project Documentation (Landing Page)

```markdown
# Codex-GUI Documentation

Welcome to the documentation hub for **Codex-GUI** - a PySide6 graphical frontend for [OpenAI's Codex CLI](https://github.com/openai/codex).

This app transforms the CLI-based Codex experience into a rich, extensible desktop GUI with real-time code assistance, agent control, and execution support.

---

## Contents

- [Overview](#overview)
- [Launching](#launching)
- [Architecture](#architecture)
- [UI Components](#ui-components)
- [IDE Layout](#ide-layout)
- [Agent System](#agent-system)
- [Tool Execution](#tool-execution)
- [Plugin/Extension Support](#planned-pluginextension-support)
- [Custom Agents/Plugins](#custom-agentsplugins)
- [Roadmap](#roadmap)
- [FAQ](#faq)

---

## Overview

Codex-GUI is designed for developers who want a more interactive experience with Codex. Instead of typing in a terminal, you can now:

- Use agents to control behavior (e.g. Python-focused, refactor-only, DevOps helper)
- Generate and test code live inside a `tools/` sandbox
- Visualize file context, syntax, and output
- Manage prompt history and multi-tab sessions (History -> Clear)

---

## Launching {#launching}

1. Install [`uv`](https://github.com/astral-sh/uv).
2. Ensure Node.js **22+** is installed and available on your `PATH`.
3. Verify the **Codex CLI** is available by running `codex --help`. If it fails, install it globally with `npm install -g @openai/codex`.
4. From the `gui_pyside6` folder run:

```bash
uv pip install -r requirements.uv.in
./run.sh  # Windows: run.bat
```
On Windows the batch script will retry the Codex CLI install using `registry.npmmirror.com` if the first attempt fails.

The launcher creates `~/.hybrid_tts/venv` (Windows: `%USERPROFILE%\.hybrid_tts\venv`)
on first run if no virtual environment is active and reuses it on subsequent
launches. Dependencies are only reinstalled when `requirements.uv.in` changes.
Delete this folder to start fresh or edit the `VENV_DIR` variable in
`run.*` to move it elsewhere.

---

## Architecture

```
+--------------+
|  PySide6 UI  | <-- User Interface Layer
+--------------+
      |
+-----------+
| Backend   | <-- Codex Adapter (calls CLI functions)
| Manager   |
+-----------+
      |
+---------------------+
| Codex CLI Wrapper   | <-- CLI compatibility layer
+---------------------+
```

Key modules:
- `backend/codex_adapter.py`: Manages Codex CLI subprocesses, logging, output parsing
- `ui/`: PySide6 views, event handling, dialogs
- `utils/`: Environment detection, file I/O, path helpers

---

## UI Components

| Component       | Description |
|----------------|-------------|
| Prompt Editor  | Main text input + response area |
| Agent Switcher | Choose Codex personalities |
| Tool Panel     | View/edit Codex-generated files |
| Settings Dialog| Control temperature, model, provider, penalties and approval modes |
| Debug Console  | Dockable log viewer for stdout/stderr |
| History Panel  | View past responses and clear them |
| Images List    | Attach images via drag-and-drop |
| Files List     | Choose which project files to pass to Codex |

All components are modular for future plugins.

The settings dialog also lets you pick the provider and model, adjust top-p,
frequency/presence penalties, toggle auto-edit or full-auto modes, set the
reasoning effort, and enable flex mode.

Enable **Verbose Mode** in the settings dialog to print the final CLI command before each run.
Quiet mode suppresses progress output and reduces logging noise. Full Context passes the entire chat history to the CLI using the `--full-context` flag.
To enable these modes, tick **Quiet Mode** or **Full Context** in the Settings dialog.
```python
self.quiet_check = QCheckBox("Quiet Mode")
self.full_context_check = QCheckBox("Full Context")
```

### Session History

Use **History -> Browse Sessions** to open a list of saved sessions from
`~/.codex/sessions`. Pick a session to **View** its rollout (runs the CLI with
`--view`) or **Resume** it which inserts the prompt `Resume this session: <file>`
and starts a new Codex run.

### Image Attachments

Drag image files onto the **Images** list or click **Add Image** to attach screenshots or diagrams to your prompt. Selected files are passed to the CLI using the `--image` flag.

---

## IDE Layout

The main window uses a horizontal splitter:

- **Left panel** - agent list and current description.
- **Center panel** - prompt editor with streaming output beneath.
- **Right panel** - scrollable history of the session.

Run and Stop actions appear in both a toolbar at the top and a button bar below
the editor. The bottom status bar shows the active agent and session updates.
If the CLI fails, its stderr messages are printed in the output panel.
Detailed stdout and stderr are also routed to the **Debug Console**.
Both the left and right panels as well as the console can be shown or hidden via
the **View** menu, and the console lets you filter by errors or info.

---

## Agent System

Agents are JSON-defined behaviors stored under `resources/agents/`. Each includes:

- `name`
- `description`
- `system_prompt`
- Temperature, tool access, execution settings

See [`AGENTS.md`](../AGENTS.md) for structure and editing instructions.

---

## Tool Execution

Codex-generated scripts are saved to the `/tools/` folder.

Use the **Tools** button in the main window to open a panel that lists these scripts.
Select a file and click **Run** to execute it. Standard output and errors appear in
the panel's log view. Optionally choose a backend name from the drop-down before
running to trigger `ensure_backend_installed()` for that backend.

Security: No script is run unless the user explicitly clicks **Run**.

---

## File Context Detection

At startup the GUI scans the current working directory for common source files
(Python, JavaScript, Rust, etc.) and automatically populates the **Files** list
with any matches. This behaviour is controlled by the **Auto Scan Files**
setting in the Settings dialog.

Use **Add File** to include additional paths or **Remove** to exclude them.
When a Codex session is launched these selected files are passed to the CLI via
`--file` flags so Codex can read them as context.

---

## Login & Free Credits

The **Help** menu provides two account actions (relevant when using the OpenAI provider):

- **Login** - runs `codex --login` and opens your browser so you can authenticate
  with your OpenAI account.
- **Redeem Free Credits** - runs `codex --free` to claim any promotional credits
  tied to your account.

The API key dialog now includes a **Get API Key** link that opens your OpenAI account page.

Command output appears in the main panel and is also logged in the Debug Console.

---

## Debug Console

The Debug Console is a dockable window that shows stdout and stderr from Codex
and tools. Toggle it from **View -> Debug Console**. Use the **Info** and
**Errors** checkboxes to filter messages and click **Clear** to wipe the log.

---

## Planned Plugin/Extension Support

Planned plugin architecture will allow:

- Community-created tools (e.g. formatters, linters)
- Language-specific presets (e.g. Rust, Go)
- Agent hot-swapping via API
- Custom GUI panels via Python modules

Plugins live in `gui_pyside6/plugins/` and use a manifest system.

Current examples:

- **Syntax Formatter** - adds a button that formats the prompt using Black.
- **Agent Logger** - saves prompts and responses to `agent_log.txt` when enabled.
- **TTS Player** - speaks the current prompt using gTTS (disabled by default).

---

## Custom Agents/Plugins {#custom-agentsplugins}

- **Agents**: Drop a JSON file into `resources/agents/`. New files are loaded on startup.
- **Plugins**: Place your module inside `gui_pyside6/plugins/` and list it in `plugins/manifest.json`. Only entries with `"enabled": true` are imported.
- **Interface**: Each plugin exports a `register(window)` function which receives the main window instance so you can add widgets or hook signals.
  - Some plugins require additional packages. The helper `ensure_backend_installed()` first checks if you are running inside a virtual environment. If not, it creates a user-scoped environment at `~/.hybrid_tts/venv` (Windows: `%USERPROFILE%\.hybrid_tts\venv`) and installs the dependencies there. This directory is reused across launches. Activate your own virtual environment before starting the app if you want packages installed elsewhere.

---

## Plugin Manager

Open **Plugins -> Plugin Manager** to enable or disable optional plugins listed in `plugins/manifest.json`. Each entry appears with a checkbox. Click **Save** to persist your choices and reload the plugins immediately.

---

## Roadmap (Q3-Q4 2025)

- [x] Basic GUI shell (prompt, agent, response)
- [x] Load/save agents
- [x] Run CLI subprocess and parse output
- [x] Add file-aware completions
- [x] Build debug panel (logs, errors, console)
- [ ] Execution in `uv` sandbox
- [x] Plugin manager
- [x] Drag-and-drop file attachments
- [x] Quiet & full-context CLI flags
- [x] Tools panel for running generated scripts
- [x] Session history browser and resume support
- [x] Editable agents via dialog
- [x] Provider/model selection and CLI path settings
- [x] API key login and credit redemption helpers

---

## FAQ

**Q: Is this officially supported by OpenAI?**  
A: No - this is a community project built on their CLI.

**Q: Can I use my own Codex API key?**  
A: Yes - support for `.env` and GUI-based key config is planned.

**Q: Does this modify Codex's output?**  
A: No - it wraps the CLI and displays output cleanly with added controls.

---

Want to contribute? See [CONTRIBUTING.md](../CONTRIBUTING.md)
```

---
