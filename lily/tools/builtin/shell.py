"""Run a shell command in Termux."""
import subprocess

from lily.tools.base import BaseTool, to_int
from lily.utils.errors import ToolError
from lily.utils.paths import workplace


class Tool(BaseTool):
    name = "shell"
    description = "Run a shell command on the phone (Termux). Returns the exit code and output."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "the command to run"},
            "timeout": {"type": "integer", "description": "seconds before it is stopped (default 30, max 120)"},
        },
        "required": ["command"],
    }

    def run(self, command, timeout=30):
        limit = max(1, min(to_int(timeout, "timeout", 30), 120))
        try:
            done = subprocess.run(
                command, shell=True, capture_output=True, text=True, errors="replace",
                stdin=subprocess.DEVNULL, timeout=limit, cwd=workplace(),
            )
        except subprocess.TimeoutExpired:
            raise ToolError(f"the command was stopped after {limit} seconds") from None
        output = (done.stdout + done.stderr).strip()
        return f"exit code {done.returncode}\n{output}"
