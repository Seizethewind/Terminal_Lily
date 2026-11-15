"""Read a text file."""
from pathlib import Path

from lily.tools.base import BaseTool, to_int
from lily.utils.errors import ToolError

MAX_BYTES = 2_000_000


class Tool(BaseTool):
    name = "read_file"
    description = "Read a text file. Use offset (characters to skip) to continue a long file."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "file path (~ is allowed)"},
            "offset": {"type": "integer", "description": "characters to skip, default 0"},
        },
        "required": ["path"],
    }

    def run(self, path, offset=0):
        file = Path(path).expanduser()
        if not file.is_file():
            raise ToolError(f"not a file: {file}")
        try:
            if file.stat().st_size > MAX_BYTES:
                raise ToolError(f"{file} is larger than {MAX_BYTES} bytes")
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError as err:
            raise ToolError(f"cannot read {file}: {err}") from err
        return text[to_int(offset, "offset", 0):]
