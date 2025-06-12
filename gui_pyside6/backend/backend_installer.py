"""Utility for installing optional backend dependencies."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import venv
from pathlib import Path


_REQUIREMENTS_PATH = Path(__file__).resolve().parent / "backend_requirements.json"


def _load_requirements() -> dict[str, list[str]]:
    if not _REQUIREMENTS_PATH.exists():
        return {}
    try:
        with _REQUIREMENTS_PATH.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Failed to read {_REQUIREMENTS_PATH}: {exc}")
        return {}


def _ensure_venv(path: Path) -> Path:
    """Create a virtual environment at the given path if it doesn't exist."""
    python_path = path / ("Scripts" if os.name == "nt" else "bin") / "python"
    if not python_path.exists():
        builder = venv.EnvBuilder(with_pip=True)
        builder.create(path)
    return python_path


def ensure_backend_installed(backend_name: str) -> None:
    """Install optional packages for the given backend if needed."""
    requirements = _load_requirements()
    packages = requirements.get(backend_name)
    if not packages:
        return

    if sys.prefix != sys.base_prefix:
        python = Path(sys.executable)
    else:
        venv_dir = Path.home() / ".hybrid_tts" / "venv"
        python = _ensure_venv(venv_dir)

    cmd = [str(python), "-m", "pip", "install", *packages]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as exc:
        print(f"Failed to install packages for {backend_name}: {exc}")

