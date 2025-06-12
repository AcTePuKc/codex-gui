"""Codex CLI interaction helpers."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable

__all__ = ["start_session", "stop_session"]

# Global process handle for the currently running Codex session
_current_process: subprocess.Popen[str] | None = None
# Indicates whether stop_session() was invoked
_terminated: bool = False


def start_session(prompt: str, agent: dict) -> Iterable[str]:
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

    cmd = ["codex"]

    # Map agent dictionary keys to Codex CLI flags
    flag_map = {
        "temperature": "--temperature",
        "default_temperature": "--temperature",
        "max_tokens": "--max-tokens",
        "top_p": "--top-p",
        "frequency_penalty": "--frequency-penalty",
        "presence_penalty": "--presence-penalty",
        "model": "--model",
    }

    for key, flag in flag_map.items():
        if key in agent:
            cmd.extend([flag, str(agent[key])])

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
