import subprocess
from pathlib import Path
import sys
import os
from collections.abc import Callable

from .backend_installer import ensure_backend_installed


def run_tool_script(
    script_path: Path,
    env_path: Path | None = None,
    backend_name: str | None = None,
    log_fn: Callable[[str, str], None] | None = None,
) -> tuple[int, str, str]:
    """Run a Python script from the /tools folder, installing backend deps."""
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    if backend_name:
        if log_fn:
            log_fn(f"Ensuring backend '{backend_name}' is installed", "info")
        ensure_backend_installed(backend_name)

    cmd = [sys.executable, str(script_path)]
    if log_fn:
        log_fn("$ " + " ".join(cmd), "info")

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
    if stdout and log_fn:
        for line in stdout.splitlines():
            log_fn(line, "info")
    if stderr and log_fn:
        for line in stderr.splitlines():
            log_fn(line, "error")
    return process.returncode, stdout, stderr

