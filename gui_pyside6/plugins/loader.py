import importlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

# Path to the manifest relative to this file
_MANIFEST_PATH = Path(__file__).resolve().parent / "manifest.json"


def _import_module(entry: str) -> ModuleType | None:
    """Import a plugin module given its entry path."""
    module_path = Path(entry)
    # Convert entry like "plugins/syntax_formatter.py" to
    # "gui_pyside6.plugins.syntax_formatter"
    parts = module_path.with_suffix("").parts
    module_name = ".".join(("gui_pyside6", *parts))
    try:
        return importlib.import_module(module_name)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Failed to import plugin {module_name}: {exc}")
        return None


def load_plugins(main_window: Any) -> None:
    """Load and register enabled plugins into the given main window."""
    if not _MANIFEST_PATH.exists():
        return

    try:
        with _MANIFEST_PATH.open("r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Failed to read plugin manifest: {exc}")
        return

    for plugin in manifest.get("plugins", []):
        if not plugin.get("enabled", False):
            continue

        entry = plugin.get("entry")
        if not entry:
            continue

        module = _import_module(entry)
        if not module:
            continue

        register = getattr(module, "register", None)
        if callable(register):
            try:
                register(main_window)
            except Exception as exc:  # pylint: disable=broad-except
                print(f"Plugin {entry} failed during register(): {exc}")
