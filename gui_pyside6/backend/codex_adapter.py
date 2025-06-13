"""Codex CLI interaction helpers."""

from __future__ import annotations

import os
import subprocess
import shutil
import shlex
from pathlib import Path
from collections.abc import Iterable, Callable

from .settings_manager import save_settings


class CodexError(RuntimeError):
    """Raised when the Codex CLI exits with an error."""

    def __init__(self, return_code: int, stderr: str) -> None:
        super().__init__(f"Codex CLI exited with code {return_code}")
        self.return_code = return_code
        self.stderr = stderr


class CodexTimeout(RuntimeError):
    """Raised when a Codex CLI command exceeds the allowed timeout."""

    def __init__(self, timeout: float) -> None:
        super().__init__(f"Codex CLI command timed out after {timeout} seconds")
        self.timeout = timeout


__all__ = [
    "start_session",
    "stop_session",
    "login",
    "redeem_free_credits",
    "ensure_cli_available",
    "CodexError",
    "CodexTimeout",
    "build_command",
]

# Global process handle for the currently running Codex session
_current_process: subprocess.Popen[str] | None = None
# Indicates whether stop_session() was invoked
_terminated: bool = False


def ensure_cli_available(
    settings: dict | None = None,
    log_fn: Callable[[str, str], None] | None = None,
) -> None:
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

    if log_fn:
        paths_txt = ", ".join(candidates) or "<none>"
        log_fn(f"Searching CLI paths: {paths_txt}", "info")

    for path in candidates:
        try:
            subprocess.run(
                shlex.split(str(path)) + ["--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                text=True,
            )
            if path == cli_path:
                if log_fn:
                    log_fn(f"Using configured CLI path: {path}", "info")
                return
            if log_fn:
                log_msg = "Using detected CLI path: {}".format(path)
                if cli_path:
                    log_msg += " (replacing invalid setting)"
                else:
                    log_msg += " (no previous setting)"
                log_fn(log_msg, "info")
            settings["cli_path"] = path
            try:
                save_settings(settings)
            except Exception:  # pylint: disable=broad-except
                pass
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue

    npx_path = shutil.which("npx")
    if npx_path:
        if log_fn:
            log_fn("Attempting 'npx codex --help' fallback", "info")
        try:
            subprocess.run(
                [npx_path, "codex", "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
                text=True,
            )
            cli_cmd = "npx codex --no-update-notifier"
            if log_fn:
                log_msg = f"Using '{cli_cmd}' fallback"
                if cli_path:
                    log_msg += " (replacing invalid setting)"
                else:
                    log_msg += " (no previous setting)"
                log_fn(log_msg, "info")
            settings["cli_path"] = cli_cmd
            try:
                save_settings(settings)
            except Exception:  # pylint: disable=broad-except
                pass
            return
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass

    raise FileNotFoundError(
        "Codex CLI is missing. Install it with 'npm install -g @openai/codex' or set the path in Settings. "
        "See README.md#first-time-setup for manual setup steps."
    )


def build_command(
    prompt: str,
    agent: dict,
    settings: dict | None = None,
    view: str | None = None,
    images: list[str] | None = None,
    files: list[str] | None = None,
    cwd: str | None = None,
) -> list[str]:
    """Construct the Codex CLI command from agent and settings.

    Parameters
    ----------
    cwd : str | None, optional
        Working directory for the Codex process. Included for convenience but
        not used directly when building the argument list.
    """
    settings = settings or {}

    cli_exe = settings.get("cli_path") or "codex"
    cmd: list[str] = shlex.split(str(cli_exe))
    if settings.get("use_uv_sandbox"):
        cmd = ["uv", "run", *cmd]

    def add_flag(flag: str, value: object | None) -> None:
        """Safely append a flag and value to the command list."""
        if value is None or isinstance(value, bool):
            return
        value_str = str(value)
        if value_str:
            cmd.extend([flag, value_str])

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
    if writable_root and not isinstance(writable_root, bool):
        if isinstance(writable_root, str):
            roots = [r for r in writable_root.split(os.pathsep) if r]
        else:
            try:
                roots = list(writable_root)
            except TypeError:
                roots = []
        for root_path in roots:
            if root_path is None or isinstance(root_path, bool):
                continue
            root_str = str(root_path)
            if root_str:
                cmd.extend(["--writable-root", root_str])

    if view and not isinstance(view, bool):
        view_str = str(view)
        if view_str:
            cmd.extend(["--view", view_str])

    if images:
        for img in images:
            if not img or isinstance(img, bool):
                continue
            img_str = str(img)
            if img_str:
                cmd.extend(["--image", img_str])

    if files:
        for path in files:
            if not path or isinstance(path, bool):
                continue
            path_str = str(path)
            if path_str:
                cmd.extend(["--file", path_str])

    cmd.append(str(prompt))
    return cmd


def start_session(
    prompt: str,
    agent: dict,
    settings: dict | None = None,
    view: str | None = None,
    images: list[str] | None = None,
    files: list[str] | None = None,
    cwd: str | None = None,
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
    cwd: str | None, optional
        Working directory to run the Codex process in.

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
        cwd=cwd,
    )
    _terminated = False
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        cwd=cwd,
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


def _run_simple_command(cmd: list[str], timeout: float | None = None) -> Iterable[str]:
    """Run a Codex CLI command and yield output lines."""
    global _current_process
    if _current_process is not None:
        raise RuntimeError("A Codex session is already running")

    if timeout is not None and timeout <= 0:
        raise ValueError("timeout must be positive")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise CodexTimeout(timeout or 0) from exc

    if result.returncode != 0:
        raise CodexError(result.returncode, result.stderr)

    for line in result.stdout.splitlines():
        yield line.rstrip("\n")


def login(settings: dict | None = None) -> Iterable[str]:
    """Run ``codex --login`` and yield output lines."""
    settings = settings or {}
    cli_exe = settings.get("cli_path") or "codex"
    cmd = shlex.split(str(cli_exe)) + ["--login"]
    if settings.get("use_uv_sandbox"):
        cmd = ["uv", "run", *cmd]
    yield from _run_simple_command(cmd)


def redeem_free_credits(
    settings: dict | None = None,
    *,
    timeout: float | None = None,
) -> Iterable[str]:
    """Run ``codex --free`` and yield output lines.

    Parameters
    ----------
    timeout : float | None, optional
        Maximum number of seconds to allow the command to run before
        terminating it. ``None`` will use the ``redeem_timeout`` setting or
        the default of 30 seconds.
    """
    settings = settings or {}
    if timeout is None:
        timeout = float(settings.get("redeem_timeout", 30))
    cli_exe = settings.get("cli_path") or "codex"
    cmd = shlex.split(str(cli_exe)) + ["--free"]
    if settings.get("use_uv_sandbox"):
        cmd = ["uv", "run", *cmd]
    yield from _run_simple_command(cmd, timeout=timeout)
