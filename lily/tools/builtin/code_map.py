"""Show the files and functions of a folder, to find the right file in a big project."""
from lily.tools import symbols
from lily.tools.base import BaseTool
from lily.utils.errors import ToolError
from lily.utils.paths import in_workplace


class Tool(BaseTool):
    name = "code_map"
    description = (
        "List the files in a folder with their classes and functions (Python, JavaScript, Go, Rust, Java, "
        "Kotlin and more, plus Markdown headings). Use it before reading files in a big folder. "
        "Give find to keep only files or functions that contain that word."
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "folder (a relative path starts in the workplace), default is the workplace"},
            "find": {"type": "string", "description": "only show files or functions containing this word (optional)"},
        },
    }

    def run(self, path=".", find=""):
        folder = in_workplace(path)
        if not folder.is_dir():
            raise ToolError(f"not a folder: {folder}")
        return symbols.build_map(folder, str(find or ""))
