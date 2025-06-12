import subprocess
from pathlib import Path
import sys
import os

from .backend_installer import ensure_backend_installed


def run_tool_script(
    script_path: Path,
    env_path: Path | None = None,
    backend_name: str | None = None,
) -> tuple[int, str, str]:
    """Run a Python script from the /tools folder, installing backend deps."""
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    if backend_name:
        ensure_backend_installed(backend_name)

    cmd = [sys.executable, str(script_path)]

    env = None
    if env_path:
        env = {"VIRTUAL_ENV": str(env_path), **os.environ}

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr
