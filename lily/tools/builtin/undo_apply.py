"""Tool: put back the files the last apply replaced (asks the user first)."""
from lily.self import access
from lily.tools.base import BaseTool
from lily.utils.errors import ToolError


class Tool(BaseTool):
    name = "undo_apply"
    description = "Undo the last apply: put the old files back. Files edited since are left alone."
    parameters = {"type": "object", "properties": {}}

    def run(self):
        staging = access.need_staging(self.lily)
        if not self.lily.confirm("Lily wants to undo the last apply (the old files come back)."):
            raise ToolError("the user declined the undo")
        return staging.undo()
