"""Tool: throw away staged files that were not applied."""
from lily.self import access
from lily.tools.base import BaseTool


class Tool(BaseTool):
    name = "discard_changes"
    description = "Drop one staged file, or all of them, without saving."
    parameters = {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "one staged file (optional)"}},
    }

    def run(self, path=None):
        return access.need_staging(self.lily).discard(path)
