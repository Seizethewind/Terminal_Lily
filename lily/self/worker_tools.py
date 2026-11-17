"""The tools a worker may use. Anything that is not read-only waits for the user's approval."""
from lily.tools.describe import describe
from lily.utils.errors import LilyError, ToolError

SAFE = {"read_file", "web_search", "rag_search"}                        # run without asking
LILY_ONLY = {"delegate", "task_status", "approve_task", "remember"}    # workers must not use these
CLIP = 4000


class WorkerTools:
    name = "tools"

    def __init__(self, lily, hive, task_id, wait):
        self.lily, self.hive, self.task_id, self.wait = lily, hive, task_id, wait

    def _registry(self):
        tools = self.lily.router.get("tools")
        if tools is None:
            raise ToolError("the tools layer is not installed")
        return tools.registry

    def schemas(self):
        try:
            found = self._registry().schemas()
        except ToolError:
            return None
        return [item for item in found if item["function"]["name"] not in LILY_ONLY] or None

    def run(self, state, call, **kwargs):
        name, args = call["name"], call.get("args") or {}
        tool = None if name in LILY_ONLY else self._registry().get(name)
        if tool is None:
            raise ToolError(f"no tool named '{name}' is available to workers")
        if name not in SAFE and not self._approved(tool, args):
            self.hive.note(self.task_id, f"{name}: the user did not approve")
            raise ToolError(f"the user did not approve {name}")
        self.hive.note(self.task_id, f"using {name}")
        try:
            return tool.execute(args)[:CLIP]
        except LilyError:
            raise
        except Exception as err:   # noqa: BLE001 - a buggy tool must not crash the worker
            raise ToolError(f"{name} crashed: {err}") from err

    def _approved(self, tool, args):
        what, details = describe(tool.name, args)
        text = what + (f": {details[0]}" if details else "")
        return self.hive.request(self.task_id, text, self.wait)
