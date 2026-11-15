"""The interface every tool follows (built-in tools, plugins and MCP tools)."""
from lily.utils.errors import ToolError


def to_int(value, name, default=None):
    """Models sometimes send numbers as strings; turn them into an int."""
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ToolError(f"'{name}' must be a whole number, got {value!r}") from None


class BaseTool:
    name = ""
    description = ""
    parameters = {"type": "object", "properties": {}}   # JSON Schema of the arguments

    def __init__(self, lily):
        self.lily = lily

    def run(self, **args):
        """Do the work and return the result as text."""
        raise NotImplementedError

    def schema(self):
        """The OpenAI-style definition offered to the model."""
        fn = {"name": self.name, "description": self.description, "parameters": self.parameters}
        return {"type": "function", "function": fn}

    def execute(self, args):
        self.check(args)
        return str(self.run(**args))

    def check(self, args):
        """Refuse calls with missing or unexpected arguments."""
        missing = [key for key in self.parameters.get("required", []) if key not in args]
        if missing:
            raise ToolError(f"{self.name}: missing argument(s): {', '.join(missing)}")
        if "properties" in self.parameters:
            unknown = [key for key in args if key not in self.parameters["properties"]]
            if unknown:
                raise ToolError(f"{self.name}: unknown argument(s): {', '.join(unknown)}")
