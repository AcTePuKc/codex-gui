## 🤖 `AGENTS.md` – Agent Configuration & System Logic

```markdown
# Agents in Codex-GUI

This document defines how **agents** are structured, configured, and used within the GUI.

## 💡 What is an Agent?

An *agent* is a combination of:
- **System prompt**
- **User instructions**
- **Behavioral presets** (temperature, tools, coding style, etc.)
- Optionally: command execution capabilities or filesystem sandbox

Agents simulate various personalities or coding roles (e.g. "Python Expert", "Refactor Bot", "Bug Hunter").

## 🧠 Agent Preset Format

Presets are stored as `.json` files (or `.toml` in future), located in:

```

resources/agents/

````

Example:

```json
{
  "name": "Python Expert",
  "description": "Writes clean, idiomatic Python code and can create and debug full scripts.",
  "system_prompt": "You are a professional Python developer...",
  "default_temperature": 0.5,
  "tools_enabled": true
}
````

## 🧩 Tooling Support

Each agent can optionally access a `tools/` folder in the project root.

* This is a **sandbox directory** where Codex can:

  * Save test scripts
  * Run/debug code
  * View output or logs

Example workflow:

* User prompts Codex to "Create a JSON validator tool"
* Agent generates file into `tools/json_validator.py`
* Codex GUI allows user to **preview, edit, or run** the file with optional logging

> ✅ File operations will be visible to the user. GUI never executes arbitrary code unless explicitly requested.

## ⚙️ Execution Policy

* Scripts are run using `uv` environments if available
* Optional support for Miniconda/conda environments
* CLI backend ensures sandboxing and terminal log output

## 🔄 Agent Switching

Users can:

* Switch agents per tab
* Save new custom agent configs via the UI
* Load previously saved agents from dropdown
* Export/import agent bundles

---

## 📌 Planned Agent Types

| Agent Name      | Description                                 |
| --------------- | ------------------------------------------- |
| Python Expert   | Best practices, modern syntax, full scripts |
| Refactor Pro    | Cleans up and improves existing code        |
| DevOps Buddy    | Bash, Docker, CLI tasks                     |
| JS Wizard       | Frontend, Node.js, toolchains               |
| Ask Me Anything | Chatty, non-technical QA                    |

---

### Note
* Codex-GUI and Codex-CLI are developed in parallel but live in different folders.
* Changes to one shouldn't interfere with the other. Keep CLI logic in the root, and GUI in `gui_pyside6/`.
---

*Reminder:* `gui_pyside6/` is for the PySide6 GUI only. Keep CLI-related scripts and logic at the root level.

For backend integration, see `backend/agent_manager.py`.

---