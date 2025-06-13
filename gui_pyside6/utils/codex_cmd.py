from __future__ import annotations

import os
from pathlib import Path

__all__ = ["create_codex_cmd", "path_in_env"]


def create_codex_cmd(directory: str | Path) -> Path:
    """Create ``codex.cmd`` in *directory* invoking ``npx codex``.

    Returns the path to the created file.
    """
    path = Path(directory).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    cmd_file = path / "codex.cmd"
    with cmd_file.open("w", encoding="utf-8") as fh:
        fh.write("@echo off\n")
        fh.write("npx codex --no-update-notifier %*\n")
    return cmd_file


def path_in_env(directory: str | Path) -> bool:
    """Return ``True`` if *directory* is in the ``PATH`` environment variable."""
    directory = str(Path(directory).resolve())
    parts = os.environ.get("PATH", "").split(os.pathsep)
    return any(Path(p).resolve() == Path(directory) for p in parts if p)
