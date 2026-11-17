"""Tool: hand a job to a background worker so Lily can keep chatting."""
from lily.self import access
from lily.tools.base import BaseTool


class Tool(BaseTool):
    name = "delegate"
    description = (
        "Give a job to a background worker and keep chatting. Returns a task number at once; "
        "check progress with task_status."
    )
    parameters = {
        "type": "object",
        "properties": {
            "role": {"type": "string", "description": "researcher, coder, summarizer, or another short role"},
            "task": {"type": "string", "description": "A clear and complete description of the job"},
        },
        "required": ["role", "task"],
    }

    def run(self, role, task):
        return access.of(self.lily).delegate(str(role), str(task))
