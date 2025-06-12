import subprocess
from pathlib import Path
import sys

def run_tool_script(script_path: Path, env_path: Path | None = None) -> tuple[int, str, str]:
    """Runs a Python script from the /tools folder."""
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

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
