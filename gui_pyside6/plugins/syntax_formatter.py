"""Plugin that adds a Format button to the main window."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtWidgets import QPushButton


def _ensure_black() -> None:
    """Ensure the ``black`` package is available."""
    try:
        import black  # type: ignore  # noqa: F401
    except Exception:  # pylint: disable=broad-except
        subprocess.check_call([sys.executable, "-m", "pip", "install", "black"])


def _format_text(text: str) -> tuple[str | None, str | None]:
    """Format the given Python code using ``black``."""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".py") as tmp:
        tmp.write(text)
        tmp.flush()
        tmp_path = Path(tmp.name)

    result = subprocess.run(
        [sys.executable, "-m", "black", "-q", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        error = result.stderr.strip() or "Formatting failed"
        tmp_path.unlink(missing_ok=True)
        return None, error
    formatted = tmp_path.read_text(encoding="utf-8")
    tmp_path.unlink(missing_ok=True)
    return formatted, None


def register(window) -> None:
    """Register the plugin with the main window."""
    _ensure_black()

    button = QPushButton("Format")
    window.button_bar.addWidget(button)

    def on_click() -> None:
        original = window.prompt_edit.toPlainText()
        if not original.strip():
            return
        try:
            formatted, error = _format_text(original)
        except Exception as exc:  # pylint: disable=broad-except
            window.output_view.appendPlainText(f"Format error: {exc}")
            return
        if error:
            window.output_view.appendPlainText(f"Format error: {error}")
            return
        if formatted is not None:
            window.prompt_edit.setPlainText(formatted)

    button.clicked.connect(on_click)
