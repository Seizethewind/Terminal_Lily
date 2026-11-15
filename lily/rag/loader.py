"""Finds and reads the files to index."""
from pathlib import Path

from lily.utils.errors import LilyError

TEXT_SUFFIXES = {
    ".txt", ".md", ".rst", ".py", ".sh", ".js", ".html", ".json", ".toml",
    ".yaml", ".yml", ".ini", ".csv", ".log", "",
}
MAX_BYTES = 1_000_000   # bigger files are skipped
MAX_FILES = 500         # one /ingest never indexes more than this


def _wanted(file, root):
    parts = file.relative_to(root).parts
    if any(part.startswith(".") for part in parts) or not file.is_file():
        return False
    return file.suffix.lower() in TEXT_SUFFIXES and file.stat().st_size <= MAX_BYTES


def find_files(path):
    """A single file, or the text files inside a folder (hidden ones are skipped)."""
    root = Path(path).expanduser()
    if root.is_file():
        return [root]
    if not root.is_dir():
        raise LilyError(f"not a file or folder: {root}")
    files = []
    for file in sorted(root.rglob("*")):
        if _wanted(file, root):
            files.append(file)
            if len(files) >= MAX_FILES:
                break
    return files


def read(file):
    """The file's text, or None if it cannot be read or is binary."""
    try:
        text = file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return None if "\x00" in text else text
