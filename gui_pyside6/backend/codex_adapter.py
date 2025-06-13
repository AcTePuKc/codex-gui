"""Codex CLI interaction helpers."""

from __future__ import annotations

import os
import subprocess
import shutil
from pathlib import Path
from collections.abc import Iterable

from .settings_manager import save_settings


class CodexError(RuntimeError):
    """Raised when the Codex CLI exits with an error."""

    def __init__(self, return_code: int, stderr: str) -> None:
        super().__init__(f"Codex CLI exited with code {return_code}")
        self.return_code = return_code
        self.stderr = stderr


__all__ = [
    "start_session",
    "stop_session",
    "login",
    "redeem_free_credits",
    "ensure_cli_available",
    "CodexError",
    "build_command",
]

# Global process handle for the currently running Codex session
_current_process: subprocess.Popen[str] | None = None
# Indicates whether stop_session() was invoked
_terminated: bool = False


def ensure_cli_available(settings: dict | None = None) -> None:
    """Verify that the Codex CLI is accessible.

    The user-configured ``cli_path`` is attempted first. If that fails, the
    system ``codex`` command is checked. On failure a ``FileNotFoundError`` is
    raised with a helpful message.
    """

    settings = settings or {}

    cli_path = settings.get("cli_path")
    candidates: list[str] = []

    if cli_path:
        candidates.append(cli_path)

    system_cmd = shutil.which("codex")
    if system_cmd:
        candidates.append(system_cmd)

    pnpm_home = os.environ.get("PNPM_HOME")
    search_dirs: list[Path] = []
    if pnpm_home:
        search_dirs.append(Path(pnpm_home))
    if os.name == "nt":
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            search_dirs.append(Path(user_profile) / "AppData" / "Local" / "pnpm")
        exe_name = "codex.cmd"
    else:
        search_dirs.append(Path.home() / ".local" / "share" / "pnpm")
        exe_name = "codex"

    for base in search_dirs:
        candidate = shutil.which(str(base / exe_name))
        if candidate:
            candidates.append(candidate)

    for path in candidates:
        try:
            subprocess.run(
                [path, "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                text=True,
            )
            if path != cli_path:
                settings["cli_path"] = path
                try:
                    save_settings(settings)
                except Exception:  # pylint: disable=broad-except
                    pass
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    raise FileNotFoundError(
        "Codex CLI is missing. Install it globally with 'npm install -g @openai/codex' "
        "or add 'codex' to your PATH."
    )


def build_command(
    prompt: str,
    agent: dict,
    settings: dict | None = None,
    view: str | None = None,
    images: list[str] | None = None,
    files: list[str] | None = None,
) -> list[str]:
    """Construct the Codex CLI command from agent and settings."""
    settings = settings or {}

    cli_exe = settings.get("cli_path") or "codex"
    cmd: list[str] = [cli_exe]

    def add_flag(flag: str, value: object | None) -> None:
        if value is not None and str(value) != "":
            cmd.extend([flag, str(value)])

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
        "provider": "--provider",
        "approval_mode": "--approval-mode",
        "reasoning": "--reasoning",
        "project_doc": "--project-doc",
    }

    bool_flags = {
        "auto_edit": "--auto-edit",
        "full_auto": "--full-auto",
        "flex_mode": "--flex-mode",
        "quiet": "--quiet",
        "full_context": "--full-context",
        "notify": "--notify",
        "no_project_doc": "--no-project-doc",
        "disable_response_storage": "--disable-response-storage",
    }

    for key, flag in flag_map.items():
        if key in agent:
            add_flag(flag, agent[key])
        elif key in settings:
            add_flag(flag, settings[key])

    model = agent.get("model", settings.get("model"))
    if model:
        cmd.extend(["--model", str(model)])

    for key, flag in bool_flags.items():
        value = agent.get(key, settings.get(key))
        if value:
            cmd.append(flag)

    writable_root = agent.get("writable_root", settings.get("writable_root"))
    if writable_root:
        if isinstance(writable_root, str):
            roots = [r for r in writable_root.split(os.pathsep) if r]
        else:
            roots = list(writable_root)
        for root_path in roots:
            cmd.extend(["--writable-root", str(root_path)])

    if view:
        cmd.extend(["--view", view])

    if images:
        for img in images:
            cmd.extend(["--image", img])

    if files:
        for path in files:
            cmd.extend(["--file", path])

    cmd.append(prompt)
    return cmd


def start_session(
    prompt: str,
    agent: dict,
    settings: dict | None = None,
    view: str | None = None,
    images: list[str] | None = None,
    files: list[str] | None = None,
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
    files: list[str] | None, optional
        Paths to include via ``--file`` flags.

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

    cmd = build_command(
        prompt,
        agent,
        settings,
        view=view,
        images=images,
        files=files,
    )
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
            raise CodexError(return_code, stderr_output)


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


def _run_simple_command(cmd: list[str]) -> Iterable[str]:
    """Run a Codex CLI command and yield output lines."""
    global _current_process, _terminated
    if _current_process is not None:
        raise RuntimeError("A Codex session is already running")

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
            raise CodexError(return_code, stderr_output)


def login(settings: dict | None = None) -> Iterable[str]:
    """Run ``codex --login`` and yield output lines."""
    settings = settings or {}
    cli_exe = settings.get("cli_path") or "codex"
    cmd = [cli_exe, "--login"]
    yield from _run_simple_command(cmd)


def redeem_free_credits(settings: dict | None = None) -> Iterable[str]:
    """Run ``codex --free`` and yield output lines."""
    settings = settings or {}
    cli_exe = settings.get("cli_path") or "codex"
    cmd = [cli_exe, "--free"]
    yield from _run_simple_command(cmd)
