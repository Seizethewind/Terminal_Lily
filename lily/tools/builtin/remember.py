"""Tool: keep a lasting fact about the user so Lily never forgets it."""
from lily.self import access
from lily.tools.base import BaseTool


class Tool(BaseTool):
    name = "remember"
    description = "Save one short, lasting fact about the user (a name, a preference, a plan) for every future chat."
    parameters = {
        "type": "object",
        "properties": {"fact": {"type": "string", "description": "One short sentence"}},
        "required": ["fact"],
    }

    def run(self, fact):
        return access.of(self.lily).remember(str(fact))
