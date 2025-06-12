"""Codex CLI interaction helpers."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable
from pathlib import Path

__all__ = ["start_session", "stop_session", "ensure_cli_available"]

# Global process handle for the currently running Codex session
_current_process: subprocess.Popen[str] | None = None
# Indicates whether stop_session() was invoked
_terminated: bool = False


def ensure_cli_available(settings: dict | None = None) -> None:
    """Verify that the Codex CLI is accessible.

    The user-configured ``cli_path`` is attempted first. If that fails,
    the system ``codex`` command and finally the bundled Node.js script are
    checked. On failure a ``FileNotFoundError`` is raised with a helpful
    message.
    """

    settings = settings or {}

    cli_path = settings.get("cli_path")
    if cli_path:
        try:
            subprocess.run(
                [cli_path, "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                text=True,
            )
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    # Try system-wide "codex" first
    try:
        subprocess.run(
            ["codex", "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True,
        )
        return
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    # Fall back to local Node.js script
    root = Path(__file__).resolve().parents[2]
    cli_js = root / "codex-cli" / "bin" / "codex.js"
    try:
        subprocess.run(
            ["node", str(cli_js), "--help"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise FileNotFoundError(
            "Codex CLI is missing. Run 'pnpm build' in the codex-cli directory "
            "or add 'codex' to your PATH."
        ) from exc


def start_session(
    prompt: str, agent: dict, settings: dict | None = None
) -> Iterable[str]:
    """Start a Codex CLI session with the given prompt and agent.

    Parameters
    ----------
    prompt: str
        The user prompt to pass to the Codex CLI.
    agent: dict
        Dictionary describing the selected agent. Keys such as
        ``temperature``, ``max_tokens``, ``top_p``, ``frequency_penalty``,
        ``presence_penalty`` and ``model`` will be converted into their
        respective ``--<flag>`` CLI options when launching the Codex process.
    settings: dict, optional
        Runtime settings loaded from ``settings_manager``. ``temperature`` and
        ``max_tokens`` from this dictionary will be applied as CLI flags if they
        are not already provided by ``agent``.

    Yields
    ------
    str
        Lines of stdout from the Codex process.

    Raises
    ------
    RuntimeError
        If a session is already running or if the Codex process exits with
        a non-zero return code.
    """
    global _current_process, _terminated

    if _current_process is not None:
        raise RuntimeError("A Codex session is already running")

    settings = settings or {}

    cli_exe = settings.get("cli_path") or "codex"
    cmd = [cli_exe]

    def add_flag(flag: str, value: object | None) -> None:
        if value is not None:
            cmd.extend([flag, str(value)])

    # Handle temperature separately to avoid duplicate flags
    if "temperature" in agent:
        add_flag("--temperature", agent["temperature"])
    elif "default_temperature" in agent:
        add_flag("--temperature", agent["default_temperature"])
    else:
        add_flag("--temperature", settings.get("temperature"))

    flag_map = {
        "max_tokens": "--max-tokens",
        "top_p": "--top-p",
        "frequency_penalty": "--frequency-penalty",
        "presence_penalty": "--presence-penalty",
        "model": "--model",
    }

    for key, flag in flag_map.items():
        if key in agent:
            add_flag(flag, agent[key])
        elif key in settings:
            add_flag(flag, settings[key])

    # Append the user prompt last
    cmd.append(prompt)
    _terminated = False
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    _current_process = process

    assert process.stdout is not None
    assert process.stderr is not None

    try:
        for line in process.stdout:
            yield line.rstrip("\n")
    finally:
        process.stdout.close()
        stderr_output = process.stderr.read()
        process.stderr.close()
        return_code = process.wait()
        _current_process = None
        if return_code != 0 and not _terminated:
            raise RuntimeError(
                f"Codex CLI exited with code {return_code}: {stderr_output.strip()}"
            )


def stop_session() -> None:
    """Terminate the running Codex session, if any."""
    global _current_process, _terminated
    if _current_process and _current_process.poll() is None:
        _terminated = True
        _current_process.terminate()
        try:
            _current_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _current_process.kill()
    _current_process = None
