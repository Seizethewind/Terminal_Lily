"""Tool: put back the files the last apply replaced (asks the user first, except at semi and full)."""
from lily.self import access
from lily.tools.base import BaseTool
from lily.utils.errors import ToolError


class Tool(BaseTool):
    name = "undo_apply"
    description = "Undo the last apply: put the old files back. Files edited since are left alone."
    parameters = {"type": "object", "properties": {}}

    def run(self):
        staging = access.need_staging(self.lily)
        question = "Lily wants to undo the last apply (the old files come back)."
        if access.level(self.lily) not in ("semi", "full") and not self.lily.confirm(question):
            raise ToolError("the user declined the undo")
        return staging.undo()
