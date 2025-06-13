"""Hybrid PySide6 GUI package."""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOG_ENABLED = os.getenv("CODEX_GUI_LOGGING", "1") != "0"

logger = logging.getLogger("gui_pyside6")
logger.setLevel(logging.INFO)

if LOG_ENABLED:
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(
        log_dir / "gui.log", maxBytes=1_000_000, backupCount=3
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(file_handler)
else:
    logger.addHandler(logging.NullHandler())

__all__ = ["logger"]
