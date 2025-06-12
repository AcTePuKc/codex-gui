from __future__ import annotations

from pathlib import Path
from typing import List

from .file_scanner import find_source_files


def get_common_paths(root: Path | str = Path.cwd(), max_files: int = 50) -> List[str]:
    """Return source file paths relative to *root* for autocompletion."""

    root_path = Path(root)
    files: List[str] = []
    for path in find_source_files(root_path, max_files=max_files):
        try:
            rel = Path(path).resolve().relative_to(root_path.resolve())
        except ValueError:
            rel = Path(path)
        files.append(str(rel))
    return files
