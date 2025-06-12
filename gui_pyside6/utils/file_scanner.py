from __future__ import annotations

from pathlib import Path
from typing import List

# File extensions considered relevant for context
EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.c', '.cpp', '.h', '.rs', '.json', '.md', '.txt'
}


def find_source_files(root: Path | str = '.', max_files: int = 50) -> List[str]:
    """Recursively discover source files under *root*.

    Only files with extensions defined in :data:`EXTENSIONS` are returned.
    The search stops after ``max_files`` results to avoid scanning huge
    directories.
    """
    root_path = Path(root)
    files: List[str] = []
    for path in root_path.rglob('*'):
        if path.suffix.lower() in EXTENSIONS and path.is_file():
            files.append(str(path))
            if len(files) >= max_files:
                break
    return files
