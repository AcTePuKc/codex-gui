"""Plugin that logs prompts and responses to a file."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime


def register(window) -> None:
    """Register the plugin with the main window."""
    log_file = Path("agent_log.txt")

    def log_prompt() -> None:
        prompt = window.prompt_edit.toPlainText()
        current = window.agent_list.currentItem()
        agent = current.text() if current else ""
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(f"\n[{datetime.now().isoformat()}] Agent: {agent}\n")
            fh.write(prompt + "\n")

    def wrap_append(original_func):
        def inner(text: str) -> None:
            with log_file.open("a", encoding="utf-8") as fh:
                fh.write(text + "\n")
            original_func(text)

        return inner

    window.run_btn.clicked.connect(log_prompt)
    window.append_output = wrap_append(window.append_output)
