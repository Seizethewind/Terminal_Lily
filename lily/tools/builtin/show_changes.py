"""Tool: list the files waiting to be saved, or show one file's change."""
from lily.self import access
from lily.tools.base import BaseTool


class Tool(BaseTool):
    name = "show_changes"
    description = "Show the staged files that wait for the user to apply them, or one file's change."
    parameters = {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "one staged file (optional)"}},
    }

    def run(self, path=None):
        return access.need_staging(self.lily).changes(path)
