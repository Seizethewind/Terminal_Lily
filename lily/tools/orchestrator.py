"""Tools sub orchestrator: look up the tool, ask permission, run it, return text."""
from lily.tools import loader
from lily.tools.mcp import adapter
from lily.tools.permissions import Permissions
from lily.tools.registry import Registry
from lily.utils.errors import LilyError, ToolError
from lily.utils.logger import get_logger
from lily.utils.paths import PLUGINS_DIR

log = get_logger("tools")
MAX_OUTPUT = 8000   # characters handed back to the model


def _clip(text):
    if not text.strip():
        return "(no output)"
    if len(text) <= MAX_OUTPUT:
        return text
    return text[:MAX_OUTPUT] + f"\n[output cut: {len(text) - MAX_OUTPUT} more characters]"


class ToolsOrchestrator:
    name = "tools"

    def __init__(self, lily, plugins_dir=PLUGINS_DIR, mcp_loader=adapter.load):
        self.lily = lily
        self.plugins_dir = plugins_dir
        self.mcp_loader = mcp_loader
        self.registry = Registry()
        self.permissions = Permissions(lily)
        self.errors = []
        self.reload()

    def reload(self):
        """(Re)load built-in tools, plugins and MCP tools. Returns a summary."""
        self.registry.clear()
        tools, self.errors = loader.load_all(self.lily, self.plugins_dir)
        mcp_tools, mcp_errors = self.mcp_loader(self.lily)
        self.errors += mcp_errors
        for tool in tools + mcp_tools:
            try:
                self.registry.register(tool)
            except ToolError as err:
                self.errors.append(str(err))
        summary = f"{len(self.registry.names())} tools loaded"
        return summary + (f", {len(self.errors)} problem(s), see /tools" if self.errors else "")

    def schemas(self):
        return self.registry.schemas()

    def describe(self):
        lines = []
        for tool in self.registry.all():
            first = (tool.description or "").strip().splitlines()[:1]
            lines.append(f"{tool.name}: {first[0] if first else ''}")
        lines += [f"problem: {err}" for err in self.errors]
        return "\n".join(lines) or "no tools loaded"

    def run(self, state, call, **kwargs):
        tool = self.registry.get(call["name"])
        if tool is None:
            known = ", ".join(self.registry.names())
            raise ToolError(f"no tool named '{call['name']}'. Available: {known}")
        args = call.get("args") or {}
        if not self.permissions.allow(tool, args, state):
            raise ToolError(f"the user declined to run {tool.name}")
        try:
            output = tool.execute(args)
        except LilyError:
            raise
        except Exception as err:   # noqa: BLE001 - a buggy tool must not crash Lily
            log.exception("tool %s crashed", tool.name)
            raise ToolError(f"{tool.name} crashed: {err}") from err
        return _clip(output)


def register(lily):
    lily.register(ToolsOrchestrator(lily))
