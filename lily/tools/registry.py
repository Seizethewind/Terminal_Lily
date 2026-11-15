"""Holds every loaded tool, by name."""
import re

from lily.utils.errors import ToolError

VALID_NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")   # what the model API accepts


class Registry:
    def __init__(self):
        self._tools = {}

    def register(self, tool):
        if not VALID_NAME.match(tool.name or ""):
            raise ToolError(f"invalid tool name {tool.name!r} (use letters, digits, _ and -)")
        if tool.name in self._tools:
            raise ToolError(f"duplicate tool name '{tool.name}'")
        self._tools[tool.name] = tool

    def get(self, name):
        return self._tools.get(name)

    def names(self):
        return list(self._tools)

    def all(self):
        return list(self._tools.values())

    def schemas(self):
        return [tool.schema() for tool in self._tools.values()]

    def clear(self):
        self._tools.clear()
