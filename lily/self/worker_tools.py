"""The tools a worker may use. Looking is free; changes wait for the user's approval."""
from lily.self import access
from lily.self.debug_guard import DebugGuard
from lily.self.rollback import Rollback
from lily.tools import policy, shell_safety, tidy
from lily.tools.describe import describe
from lily.utils.errors import LilyError, ToolError
from lily.utils.paths import in_workplace

# workers must not use these: only Lily talks to the user, saves what workers staged and restarts tasks
LILY_ONLY = {
    "delegate", "task_status", "approve_task", "remember", "retry_task",
    "apply_changes", "discard_changes", "undo_apply",
}
CLIP = 4000


class WorkerTools:
    name = "tools"

    def __init__(self, lily, hive, task_id, wait, limits=None):
        self.lily, self.hive, self.task_id, self.wait = lily, hive, task_id, wait
        self.grants = set()   # folders the user let this task save into
        limits = limits or {}
        note = lambda line: hive.note(task_id, f"command failed: {line}")   # noqa: E731
        self.guard = DebugGuard(limits.get("debug_tries", 3), note)   # stops an attempt that keeps failing
        self.rollback = Rollback(lily, limits)                         # undoes what the attempt changed

    def undo(self):
        return self.rollback.undo()

    def finish(self):
        self.rollback.discard()

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
        staged = access.staging(self.lily) is not None
        verdict = policy.decide(name, args, staged, access.level(self.lily))
        if verdict != "allow" and not self._approved(tool, args, verdict):
            self.hive.note(self.task_id, f"{name}: the user did not approve")
            raise ToolError(f"the user did not approve {name}")
        self.hive.note(self.task_id, f"using {name}")
        self._prepare(name, args)
        try:
            output = tool.execute(args)[:CLIP]
        except LilyError as err:
            if name == "shell":
                raise ToolError(f"{err}{self.guard.error(str(err))}") from err
            raise
        except Exception as err:   # noqa: BLE001 - a buggy tool must not crash the worker
            raise ToolError(f"{name} crashed: {err}") from err
        return self.guard.after(output) if name == "shell" else output

    def _prepare(self, name, args):
        """Remember what is about to change, so a failed attempt can be undone."""
        if name == "write_file":
            self.rollback.before_write(in_workplace(args.get("path", "")))
        elif name == "shell" and not shell_safety.is_read_only(args.get("command", "")):
            self.rollback.before_command()

    def _approved(self, tool, args, verdict):
        target = policy.folder(args) if verdict == "write" else None
        if target is not None and policy.covered(target, self.grants):
            return True
        what, details = describe(tool.name, args)
        text = what + (f": {tidy.short(details[0])}" if details else "")
        if target is not None:
            text += " (also covers other files in that folder for this task)"
        yes = self.hive.request(self.task_id, text, self.wait)
        if yes and target is not None:
            self.grants.add(target)
        return yes
