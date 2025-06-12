## 📚 `docs/index.md` – Full Project Documentation (Landing Page)

```markdown
# Codex-GUI Documentation

Welcome to the documentation hub for **Codex-GUI** – a PySide6 graphical frontend for [OpenAI's Codex CLI](https://github.com/openai/codex).

This app transforms the CLI-based Codex experience into a rich, extensible desktop GUI with real-time code assistance, agent control, and execution support.

---

## 🔗 Contents

- [Overview](#overview)
- [Launching](#launching)
- [Architecture](#architecture)
- [UI Components](#ui-components)
- [Agent System](#agent-system)
- [Tool Execution](#tool-execution)
- [Plugin/Extension Support](#planned-pluginextension-support)
- [Custom Agents/Plugins](#custom-agentsplugins)
- [Roadmap](#roadmap)
- [FAQ](#faq)

---

## 📦 Overview

Codex-GUI is designed for developers who want a more interactive experience with Codex. Instead of typing in a terminal, you can now:

- Use agents to control behavior (e.g. Python-focused, refactor-only, DevOps helper)
- Generate and test code live inside a `tools/` sandbox
- Visualize file context, syntax, and output
- Manage prompt history and multi-tab sessions

---

## 🚀 Launching {#launching}

1. Install [`uv`](https://github.com/astral-sh/uv).
2. From the `gui_pyside6` folder run:

```bash
uv pip install -r requirements.uv.in
./run_pyside6.sh  # Windows: run_pyside6.bat
```

---

## 🏗️ Architecture

```

┌──────────────┐
│  PySide6 UI  │ ◄─────── User Interface Layer
└─────┬────────┘
│
┌─────▼─────┐
│ Backend   │ ◄─────── Codex Adapter (calls CLI functions)
│ Manager   │
└─────┬─────┘
│
┌─────▼─────────────┐
│ Codex CLI Wrapper │ ◄────── CLI compatibility layer
└───────────────────┘

```

Key modules:
- `backend/codex_adapter.py`: Manages Codex CLI subprocesses, logging, output parsing
- `ui/`: PySide6 views, event handling, dialogs
- `utils/`: Environment detection, file I/O, path helpers

---

## 🖼️ UI Components

| Component       | Description |
|----------------|-------------|
| Prompt Editor  | Main text input + response area |
| Agent Switcher | Choose Codex personalities |
| Tool Panel     | View/edit Codex-generated files |
| Settings Dialog| Control temperature, max tokens, runtime env |
| Debug Console  | Terminal-style output window (optional) |

All components are modular for future plugins.

---

## 🧠 Agent System

Agents are JSON-defined behaviors stored under `resources/agents/`. Each includes:

- `name`
- `description`
- `system_prompt`
- Temperature, tool access, execution settings

See [`AGENTS.md`](../AGENTS.md) for structure and editing instructions.

---

## 🧪 Tool Execution

Codex-generated scripts are saved to the `/tools/` folder.

When enabled, users can:
- Preview and edit scripts
- Execute scripts inside a `uv` or `conda` environment
- View stdout/stderr from a log panel

Security: No script is run unless the user clicks “Run Tool”.

---

## 🧩 Planned Plugin/Extension Support

Planned plugin architecture will allow:

- Community-created tools (e.g. formatters, linters)
- Language-specific presets (e.g. Rust, Go)
- Agent hot-swapping via API
- Custom GUI panels via Python modules

Plugins will live in `plugins/` and use a manifest system.

Current examples:

- **Syntax Formatter** – adds a button that formats the prompt using Black.
- **Agent Logger** – saves prompts and responses to `agent_log.txt` when enabled.

---

## 🛠️ Custom Agents/Plugins {#custom-agentsplugins}

- **Agents**: Drop a JSON file into `resources/agents/`. New files are loaded on startup.
- **Plugins**: Add a Python module under `plugins/` and list it in `plugins/manifest.json`. Only entries with `"enabled": true` are imported.
- Some plugins require additional packages. The helper `ensure_backend_installed()` installs these into the active environment or `~/.hybrid_tts/venv` when needed.

---

## 🗺️ Roadmap (Q3-Q4 2025)

- [x] Basic GUI shell (prompt, agent, response)
- [x] Load/save agents
- [x] Run CLI subprocess and parse output
- [ ] Add file-aware completions
- [ ] Build debug panel (logs, errors, console)
- [ ] Execution in `uv` sandbox
- [ ] Plugin manager
- [ ] Drag-and-drop file attachments

---

## ❓ FAQ

**Q: Is this officially supported by OpenAI?**  
A: No — this is a community project built on their CLI.

**Q: Can I use my own Codex API key?**  
A: Yes — support for `.env` and GUI-based key config is planned.

**Q: Does this modify Codex’s output?**  
A: No — it wraps the CLI and displays output cleanly with added controls.

---

Want to contribute? See [CONTRIBUTING.md](../CONTRIBUTING.md)
```

---
