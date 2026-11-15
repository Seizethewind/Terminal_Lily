"""Phone features through the Termux:API app (battery, clipboard, notifications)."""
import subprocess

from lily.tools.base import BaseTool
from lily.utils.errors import ToolError

ACTIONS = ["battery", "clipboard_get", "clipboard_set", "notify", "toast"]
HINT = "In Termux run: pkg install termux-api (and install the Termux:API app)."


class Tool(BaseTool):
    name = "termux_api"
    description = "Use the phone: read the battery, get/set the clipboard, show a notification or toast."
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ACTIONS},
            "text": {"type": "string", "description": "clipboard text, notification body or toast text"},
            "title": {"type": "string", "description": "notification title (optional)"},
        },
        "required": ["action"],
    }

    def run(self, action, text="", title=""):
        if action not in ACTIONS:
            raise ToolError(f"unknown action '{action}'. Options: {', '.join(ACTIONS)}")
        if action in ("clipboard_set", "notify", "toast") and not text:
            raise ToolError(f"{action} needs the 'text' argument")
        if action == "battery":
            return self._call(["termux-battery-status"])
        if action == "clipboard_get":
            return self._call(["termux-clipboard-get"])
        if action == "clipboard_set":
            return self._call(["termux-clipboard-set"], stdin=text)
        if action == "notify":
            return self._call(["termux-notification", "--title", title or "Lily", "--content", text])
        return self._call(["termux-toast", text])

    def _call(self, command, stdin=None):
        options = {"input": stdin} if stdin is not None else {"stdin": subprocess.DEVNULL}
        try:
            done = subprocess.run(command, capture_output=True, text=True, timeout=15, **options)
        except FileNotFoundError:
            raise ToolError(f"{command[0]} was not found. {HINT}") from None
        except subprocess.TimeoutExpired:
            raise ToolError(f"{command[0]} did not answer in 15 seconds") from None
        if done.returncode != 0:
            raise ToolError(f"{command[0]} failed: {done.stderr.strip() or done.returncode}")
        return done.stdout.strip() or "done"
