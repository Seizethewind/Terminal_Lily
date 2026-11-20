"""Slash commands for tasks: /tasks and /retry."""
from lily.ui.commands import command, layer


@command("tasks", "show running workers and finished tasks")
def _tasks(lily, args):
    return layer(lily, "self").status()


@command("retry", "run a failed task again, e.g. /retry 3 (finished steps are kept)")
def _retry(lily, args):
    if not args or not args[0].isdigit():
        return "Usage: /retry <task number>"
    return layer(lily, "self").retry(int(args[0]))
