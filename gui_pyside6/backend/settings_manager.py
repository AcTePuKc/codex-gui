import json
from pathlib import Path

SETTINGS_PATH = Path("config/settings.json")

DEFAULT_SETTINGS = {
    "temperature": 0.5,
    "max_tokens": 1024,
    "selected_agent": "Python Expert"
}

def load_settings() -> dict:
    if not SETTINGS_PATH.exists():
        return DEFAULT_SETTINGS.copy()
    with SETTINGS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_settings(settings: dict) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
