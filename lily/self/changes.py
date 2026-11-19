"""Plain description of what the waiting files would change."""
import difflib
from pathlib import Path

from lily.tools import tidy

LIMIT = 3000


def _old(name):
    try:
        return Path(name).read_text(encoding="utf-8").splitlines()
    except (OSError, ValueError):
        return None


def describe(pending):
    """One line per file: new or changed, and how many lines come and go."""
    lines = []
    for name, content in sorted(pending.items()):
        new, old = content.splitlines(), _old(name)
        shown = tidy.short(name)
        if old is None:
            lines.append(f"new      {shown} (+{len(new)} lines)")
            continue
        diff = list(difflib.unified_diff(old, new, lineterm="", n=0))
        added = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
        removed = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
        label = "changed " if diff else "same    "
        lines.append(f"{label} {shown} (+{added} -{removed})")
    return lines


def diff(name, content):
    """The change to one file, cut to a phone-friendly length."""
    old = _old(name) or []
    text = "\n".join(difflib.unified_diff(old, content.splitlines(), "before", "after", lineterm=""))
    return text if len(text) <= LIMIT else text[:LIMIT] + "\n[cut]"
