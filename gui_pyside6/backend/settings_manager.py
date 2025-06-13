import json
from pathlib import Path

from .provider_loader import load_providers, save_providers

# Build the settings path relative to this module so the GUI can be started
# from any working directory.
SETTINGS_PATH = Path(__file__).resolve().parent.parent / "config" / "settings.json"

DEFAULT_SETTINGS = {
    "temperature": 0.5,
    "max_tokens": 1024,
    "provider": "openai",
    "model": "codex-mini-latest",
    "top_p": 1.0,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "approval_mode": "suggest",
    "auto_edit": False,
    "full_auto": False,
    "reasoning": "high",
    "flex_mode": False,
    "quiet": False,
    "full_context": False,
    # UI theme: "System", "Light", or "Dark"
    "theme": "System",
    "selected_agent": "Python Expert",
    # Optional path to the Codex CLI executable. If empty, the adapter will
    # search the system PATH or use the bundled Node.js script.
    "cli_path": "",
    # Print the final CLI command in the output view when running a session.
    "verbose": False,
    "notify": False,
    "project_doc": "",
    "no_project_doc": False,
    "disable_response_storage": False,
    "writable_root": "",
    # Automatically populate the file list with detected source files
    "auto_scan_files": True,
    # Timeout for the free credits command
    "redeem_timeout": 30,
}


def load_settings() -> dict:
    settings = DEFAULT_SETTINGS.copy()
    if SETTINGS_PATH.exists():
        with SETTINGS_PATH.open("r", encoding="utf-8") as f:
            try:
                loaded = json.load(f)
            except json.JSONDecodeError:
                loaded = {}
        settings.update({k: v for k, v in loaded.items() if k != "providers"})
    settings["providers"] = load_providers()
    return settings


def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {k: v for k, v in settings.items() if k != "providers"}
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    save_providers(settings.get("providers", {}))
