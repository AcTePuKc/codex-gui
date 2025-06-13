from __future__ import annotations

import json
from pathlib import Path

DEFAULT_PROVIDERS_FILE = Path(__file__).resolve().parent.parent / "resources" / "providers.json"
USER_PROVIDERS_FILE = Path(__file__).resolve().parent.parent / "config" / "providers.json"


def load_providers() -> dict:
    """Load provider mappings combining defaults with user overrides."""
    providers: dict[str, dict] = {}
    try:
        with DEFAULT_PROVIDERS_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if isinstance(data, dict):
                providers.update({k.lower(): v for k, v in data.items()})
    except Exception:
        pass
    if USER_PROVIDERS_FILE.exists():
        try:
            with USER_PROVIDERS_FILE.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
                if isinstance(data, dict):
                    providers.update({k.lower(): v for k, v in data.items()})
        except Exception:
            pass
    return providers


def save_providers(providers: dict) -> None:
    """Persist provider mappings to the user config file."""
    USER_PROVIDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with USER_PROVIDERS_FILE.open("w", encoding="utf-8") as fh:
            json.dump(providers, fh, indent=2)
    except Exception:
        pass
