"""Tool: save the staged files after the user agrees (asks once, showing the list)."""
from lily.self import access
from lily.tools.base import BaseTool
from lily.utils.errors import ToolError


class Tool(BaseTool):
    name = "apply_changes"
    description = (
        "Save all staged files into the workplace. Shows the user the file list and asks once "
        "(at semi and full autonomy it saves without asking). Call it after the user has agreed."
    )
    parameters = {"type": "object", "properties": {}}

    def run(self):
        staging = access.need_staging(self.lily)
        if staging.count() == 0:
            return "Nothing is waiting."
        if access.level(self.lily) not in ("semi", "full") and not self.lily.confirm(staging.question()):
            raise ToolError("the user declined to save the changes")
        return staging.apply()
