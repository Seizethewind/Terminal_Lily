"""Makes the 'allow?' question short and free of long phone paths."""
from pathlib import Path

LIMIT = 90


def short(text):
    text = str(text).replace(str(Path.home()), "~")
    lines = text.splitlines() or [""]
    first = lines[0] if len(lines[0]) <= LIMIT else lines[0][:LIMIT] + "..."
    return first + (f"  (+{len(lines) - 1} more lines)" if len(lines) > 1 else "")
