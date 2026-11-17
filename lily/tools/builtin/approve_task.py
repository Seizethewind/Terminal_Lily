"""Tool: pass the user's yes or no to a worker that is waiting for approval."""
from lily.self import access
from lily.tools.base import BaseTool, to_int


class Tool(BaseTool):
    name = "approve_task"
    description = (
        "Answer a worker's approval request. Only call this after the user has said yes or no "
        "to exactly that request."
    )
    parameters = {
        "type": "object",
        "properties": {
            "approval": {"type": "integer", "description": "The approval number from task_status"},
            "approve": {"type": "boolean", "description": "true if the user said yes, false if no"},
        },
        "required": ["approval", "approve"],
    }

    def run(self, approval, approve):
        yes = str(approve).strip().lower() in ("true", "yes", "y", "1")
        return access.of(self.lily).approve(to_int(approval, "approval"), yes)
