"""Makes the 'allow?' question short and free of long phone paths."""
from pathlib import Path

LIMIT = 90


def _home(text):
    return str(text).replace(str(Path.home()), "~")


def short(text):
    lines = _home(text).splitlines() or [""]
    first = lines[0] if len(lines[0]) <= LIMIT else lines[0][:LIMIT] + "..."
    return first + (f"  (+{len(lines) - 1} more lines)" if len(lines) > 1 else "")


def full(text):
    """Nothing cut. For what the user is about to approve: a 'y' must cover all of it."""
    return _home(text)
