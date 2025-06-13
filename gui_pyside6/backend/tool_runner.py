import subprocess
from pathlib import Path
import sys
import os
import time
from datetime import datetime
from collections.abc import Callable

from .. import logger

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
        msg = f"Ensuring backend '{backend_name}' is installed"
        logger.info(msg)
        if log_fn:
            log_fn(msg, "info")
        ensure_backend_installed(backend_name)

    cmd = [sys.executable, str(script_path)]
    cwd = script_path.parent
    start_ts = datetime.now()
    start = time.monotonic()

    logger.info(f"Starting tool script at {start_ts.isoformat(timespec='seconds')}")
    logger.info("$ " + " ".join(cmd))
    logger.info(f"Working directory: {cwd}")

    if log_fn:
        log_fn("$ " + " ".join(cmd), "info")
        log_fn(f"Working directory: {cwd}", "info")

    env = None
    if env_path:
        env = {"VIRTUAL_ENV": str(env_path), **os.environ}

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
        cwd=cwd,
    )

    stdout_lines: list[str] = []
    assert process.stdout is not None
    for raw_line in iter(process.stdout.readline, ""):
        line = raw_line.rstrip()
        if line:
            stdout_lines.append(line)
            logger.info(line)
            if log_fn:
                log_fn(line, "info")

    process.wait()
    duration = time.monotonic() - start
    logger.info(f"Script exited with code {process.returncode} in {duration:.2f}s")
    if log_fn:
        log_fn(f"Return code: {process.returncode} (duration {duration:.2f}s)", "info")

    stdout = "\n".join(stdout_lines)
    return process.returncode, stdout, ""

