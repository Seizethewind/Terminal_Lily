"""Tool: run a failed task again; only the steps that were not done run."""
from lily.self import access
from lily.tools.base import BaseTool, to_int


class Tool(BaseTool):
    name = "retry_task"
    description = "Run a failed task again. Steps that already finished are kept; only the rest run."
    parameters = {
        "type": "object",
        "properties": {"task": {"type": "integer", "description": "the task number from task_status"}},
        "required": ["task"],
    }

    def run(self, task):
        return access.of(self.lily).retry(to_int(task, "task"))
