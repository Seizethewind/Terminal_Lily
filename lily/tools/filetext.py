"""Reads what a file says now: the staged version if there is one, else the one on disk."""
from lily.utils.errors import ToolError


def current(file, staging):
    """The text of `file`, or None when it does not exist yet."""
    staged = staging.read(file) if staging is not None else None
    if staged is not None:
        return staged
    if not file.is_file():
        return None
    try:
        return file.read_text(encoding="utf-8")
    except (OSError, ValueError) as err:
        raise ToolError(f"cannot read {file} as text: {err}") from err
