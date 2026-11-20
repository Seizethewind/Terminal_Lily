"""Cheap syntax checks, so a broken edit never reaches the file."""
import ast
import json
import tomllib
from pathlib import Path


def error(path, text):
    """A short problem description, or None when the text parses (or the file type is not checked)."""
    suffix = Path(str(path)).suffix.lower()
    try:
        if suffix == ".py":
            ast.parse(text)
        elif suffix == ".json":
            json.loads(text)
        elif suffix == ".toml":
            tomllib.loads(text)
        else:
            return None
    except (SyntaxError, ValueError) as err:   # JSON and TOML errors are ValueErrors too
        line = getattr(err, "lineno", None)
        return f"{type(err).__name__}: {getattr(err, 'msg', err)}" + (f" (line {line})" if line else "")
    return None


def breaks(path, old, new):
    """Why `new` should be refused: it does not parse, although `old` did (or there was no old text)."""
    problem = error(path, new)
    return problem if problem and (old is None or error(path, old) is None) else None
