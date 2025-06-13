# Repository Overview

This project hosts several components that revolve around the Codex CLI and its graphical interfaces.

## Layout

- **codex-cli** – Node/TypeScript command line interface
- **codex-rs** – Rust sandbox used by the CLI
- **gui_pyside6** – active PySide6 desktop application
- **react_ui** – experimental React-based Web UI
- Root level files also contain the frozen legacy WebUI

## Available UIs

1. **Legacy WebUI** – the original Gradio-based interface (no longer maintained)
2. **PySide6 App** – the currently supported desktop GUI located in `gui_pyside6/`
3. **React UI** – a separate web project under `react_ui/`

### File Context Feature

At startup the PySide6 app scans the current working directory for common source files (Python, JavaScript, Rust, etc.). Any discovered paths appear in a **Files** list below the image attachments.

Use **Add File** to include additional paths or **Remove** to exclude them. When a Codex session is launched these selected files are passed to the CLI via `--file` flags so Codex can read them as context.

The GUI can also wrap the CLI with `uv run` by enabling **Use uv Sandbox** in the Settings dialog.

See the [PySide6 docs](../gui_pyside6/docs/index.md) for full details.
