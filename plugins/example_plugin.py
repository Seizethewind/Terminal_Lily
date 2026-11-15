"""Example plugin, and a useful tool: it tells Lily the current date and time.

To make your own tool, copy this file and change it:
  - one file = one tool: define a class named `Tool` that extends BaseTool
  - `parameters` is a JSON Schema for the arguments the model may pass
  - `run(...)` receives those arguments and returns text
  - files starting with an underscore are ignored
Then type /reload in Lily to pick up changes. Lily asks you before any tool runs.
"""
from datetime import datetime

from lily.tools.base import BaseTool


class Tool(BaseTool):
    name = "current_time"
    description = "Get the current local date and time on the phone."
    parameters = {"type": "object", "properties": {}}

    def run(self):
        return datetime.now().astimezone().strftime("%A %Y-%m-%d %H:%M:%S %Z")
