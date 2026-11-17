"""Tool: see the running workers, waiting approvals and finished tasks."""
from lily.self import access
from lily.tools.base import BaseTool


class Tool(BaseTool):
    name = "task_status"
    description = "Show the background workers, anything waiting for the user's approval, and finished tasks."
    parameters = {"type": "object", "properties": {}}

    def run(self):
        return access.of(self.lily).status()
