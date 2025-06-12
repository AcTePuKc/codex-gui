from __future__ import annotations

import os
from PySide6.QtWidgets import QWidget, QDialog

from ..ui.api_key_dialog import ApiKeyDialog


def ensure_api_key(provider: str, parent: QWidget | None = None) -> bool:
    """Ensure an API key is available for *provider*.

    Checks ``<PROVIDER>_API_KEY`` then ``OPENAI_API_KEY``. If neither is set,
    an :class:`ApiKeyDialog` is shown. The entered key is stored in the
    environment. Returns ``True`` when a key is available, ``False`` if the
    dialog was cancelled.
    """

    provider = provider.lower()
    env_var = f"{provider.upper()}_API_KEY"
    api_key = os.getenv(env_var) or os.getenv("OPENAI_API_KEY")
    if api_key:
        return True

    dialog = ApiKeyDialog(parent)
    if dialog.exec() == QDialog.Accepted:
        key = dialog.api_key()
        if key:
            os.environ[env_var] = key
            if provider == "openai":
                os.environ.setdefault("OPENAI_API_KEY", key)
            return True
    return False
