import os
from pathlib import Path
from typing import List, Dict, Any
from app.config import settings

IGNORED_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".cache", ".idea", ".vscode", "coverage"
}

SUPPORTED_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".json": "json",
    ".sql": "sql",
}

def scan_directory(target_path: str) -> List[Dict[str, Any]]:
    """
    Scans target directory recursively and returns file metadata and contents
    for supported languages.
    """
    path = Path(target_path)
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Path does not exist or is not a directory: {target_path}")

    files: List[Dict[str, Any]] = []

    for root, dirs, filenames in os.walk(path):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

        for filename in filenames:
            file_path = Path(root) / filename
            ext = file_path.suffix.lower()

            if ext in SUPPORTED_EXTENSIONS:
                try:
                    stat = file_path.stat()
                    if stat.st_size > settings.MAX_FILE_SIZE_BYTES:
                        continue

                    # Read content
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()

                    rel_path = file_path.relative_to(path).as_posix()
                    files.append({
                        "path": rel_path,
                        "absolute_path": str(file_path),
                        "language": SUPPORTED_EXTENSIONS[ext],
                        "extension": ext,
                        "size": stat.st_size,
                        "lines_count": len(content.splitlines()),
                        "content": content
                    })

                    if len(files) >= settings.MAX_SCAN_FILES:
                        return files
                except Exception as e:
                    # Ignore unreadable files
                    continue

    return files
