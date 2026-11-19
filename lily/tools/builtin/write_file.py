"""Write or append to a text file."""
from lily.tools.base import BaseTool
from lily.utils.errors import ToolError
from lily.utils.paths import in_workplace, workplace


class Tool(BaseTool):
    name = "write_file"
    description = "Write text to a file (creates folders as needed). Set append to add to the end instead."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "file path inside the workplace (a relative path starts there)"},
            "content": {"type": "string", "description": "the text to write"},
            "append": {"type": "boolean", "description": "add to the end instead of replacing"},
        },
        "required": ["path", "content"],
    }

    def run(self, path, content, append=False):
        file = in_workplace(path)
        if workplace() not in file.parents:
            raise ToolError(f"{file} is outside the workplace {workplace()}; Lily only writes there")
        try:
            file.parent.mkdir(parents=True, exist_ok=True)
            with open(file, "a" if append else "w", encoding="utf-8") as handle:
                handle.write(content)
        except OSError as err:
            raise ToolError(f"cannot write {file}: {err}") from err
        verb = "appended to" if append else "wrote"
        return f"{verb} {file} ({len(content)} characters)"
