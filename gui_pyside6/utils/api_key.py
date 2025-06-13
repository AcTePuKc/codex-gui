from __future__ import annotations

import json
import os
from pathlib import Path
from PySide6.QtWidgets import QWidget, QDialog, QInputDialog

from ..ui.api_key_dialog import ApiKeyDialog

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
KEY_FILE = CONFIG_DIR / "api_keys.json"


def _load_keys() -> dict[str, str]:
    """Return stored provider keys from :data:`KEY_FILE`."""
    if not KEY_FILE.exists():
        return {}
    try:
        with KEY_FILE.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return {k.lower(): str(v) for k, v in data.items()}
    except Exception:
        pass
    return {}


def _save_key(provider: str, key: str) -> None:
    """Persist *key* for *provider*."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _load_keys()
    data[provider.lower()] = key
    try:
        with KEY_FILE.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
    except Exception:
        pass


def ensure_api_key(provider: str, parent: QWidget | None = None) -> bool:
    """Ensure an API key is available for *provider*.

    Looks for ``<PROVIDER>_API_KEY`` or ``OPENAI_API_KEY`` in the environment.
    If not found, tries ``config/api_keys.json`` and sets the variable when a
    stored key exists. Otherwise an :class:`ApiKeyDialog` is shown. If the user
    confirms the dialog and chooses to remember the key it will be written to the
    config file. Returns ``True`` when a key is available, ``False`` if the
    dialog was cancelled.
    """

    provider = provider.lower()
    env_var = f"{provider.upper()}_API_KEY"

    api_key = os.getenv(env_var) or os.getenv("OPENAI_API_KEY")
    if not api_key:
        saved = _load_keys().get(provider)
        if saved:
            api_key = saved
            os.environ[env_var] = api_key
            if provider == "openai":
                os.environ.setdefault("OPENAI_API_KEY", api_key)

    if api_key:
        return True

    dialog = ApiKeyDialog(provider, parent)
    if dialog.exec() == QDialog.Accepted:
        key = dialog.api_key()
        if key:
            os.environ[env_var] = key
            if provider == "openai":
                os.environ.setdefault("OPENAI_API_KEY", key)
            if dialog.remember_key():
                _save_key(provider, key)
            return True
    return False


def ensure_base_url(
    provider: str,
    default_url: str | None = None,
    parent: QWidget | None = None,
) -> bool:
    """Ensure a base URL is available for *provider*.

    Checks the ``<PROVIDER>_BASE_URL`` or ``OPENAI_BASE_URL`` environment
    variables. If neither is set and *default_url* is provided it will be used.
    Otherwise the user is prompted for a URL. The chosen URL is exported via the
    provider specific variable and ``OPENAI_BASE_URL`` for the ``openai``
    provider. Returns ``True`` when a base URL is available or ``False`` if the
    dialog was cancelled.
    """

    provider = provider.lower()
    env_var = f"{provider.upper()}_BASE_URL"

    base_url = (
        os.getenv(env_var)
        or os.getenv("OPENAI_BASE_URL")
        or default_url
    )

    if base_url:
        os.environ[env_var] = base_url
        if provider == "openai":
            os.environ.setdefault("OPENAI_BASE_URL", base_url)
        return True

    url, ok = QInputDialog.getText(
        parent,
        f"{provider.capitalize()} Base URL",
        "Enter API base URL:",
    )
    if ok and url.strip():
        os.environ[env_var] = url.strip()
        if provider == "openai":
            os.environ.setdefault("OPENAI_BASE_URL", url.strip())
        return True
    return False
