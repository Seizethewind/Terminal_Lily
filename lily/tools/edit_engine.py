"""Applies a search-and-replace edit to text, forgiving the small slips weak models make."""
import difflib

from lily.utils.errors import ToolError


def _indent(line):
    return len(line) - len(line.lstrip())


def _shift(line, delta):
    if not line.strip() or delta == 0:
        return line
    return " " * delta + line if delta > 0 else line[min(-delta, _indent(line)):]


def _hint(lines, want):
    probe = next((word for word in want if word), "")
    close = difflib.get_close_matches(probe, [line.strip() for line in lines], n=1, cutoff=0.6)
    if close:
        number = next(i for i, line in enumerate(lines, 1) if line.strip() == close[0])
        return (f"the old text was not found. The closest line is {number}: {close[0][:100]}. "
                "Read the file again and copy the lines exactly.")
    return ("the old text was not found. Read the file again and copy the lines exactly, "
            "or rewrite the whole file with write_file.")


def _loose(text, old, new):
    lines = text.split("\n")
    given = old.strip("\n").split("\n")
    want = [line.strip() for line in given]
    hits = [i for i in range(len(lines) - len(want) + 1) if [line.strip() for line in lines[i:i + len(want)]] == want]
    if not hits:
        raise ToolError(_hint(lines, want))
    if len(hits) > 1:
        raise ToolError(f"the old text matches {len(hits)} places when spaces are ignored; add more surrounding lines")
    start = hits[0]
    if any("\t" in line[:_indent(line)] for line in lines[start:start + len(want)]):
        # shift() only knows spaces: guessing would mix tabs and spaces (Makefile, Go)
        raise ToolError("those lines are indented with tabs, so the edit cannot be matched loosely. "
                        "Read the file again and copy the lines exactly, tabs included.")
    delta = _indent(lines[start]) - _indent(given[0])
    fresh = [_shift(line, delta) for line in new.strip("\n").split("\n")] if new.strip("\n") else []
    return "\n".join(lines[:start] + fresh + lines[start + len(want):]), "ignoring spaces"


def apply_edit(text, old, new):
    """Returns (new text, how it matched). Exact and unique first, then ignoring indentation."""
    if not old.strip():
        raise ToolError("the old text is empty; use write_file to create or rewrite a file")
    count = text.count(old)
    if count == 1:
        return text.replace(old, new, 1), "exact"
    if count > 1:
        raise ToolError(f"the old text appears {count} times; include more surrounding lines so it is unique")
    return _loose(text, old, new)
