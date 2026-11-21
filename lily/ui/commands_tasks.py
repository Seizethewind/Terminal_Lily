"""Slash commands for the self layer: /tasks, /retry, /summary and /roles."""
from lily.ui.commands import command, layer


@command("tasks", "show running workers and finished tasks")
def _tasks(lily, args):
    return layer(lily, "self").status()


@command("retry", "run a failed task again, e.g. /retry 3 (finished steps are kept)")
def _retry(lily, args):
    if not args or not args[0].isdigit():
        return "Usage: /retry <task number>"
    return layer(lily, "self").retry(int(args[0]))


@command("summary", "show the short summary of earlier chats; /summary now refreshes it")
def _summary(lily, args):
    sub = layer(lily, "self")
    if args and args[0] == "now":
        sub.digest.update()
    return sub.memory.summary()[0] or "No summary yet: one is written after every few chats."


@command("roles", "show which model tier each job uses; /roles coder light changes one")
def _roles(lily, args):
    sub = layer(lily, "self")
    if len(args) == 2:
        sub.roles.set(args[0], args[1].lower())
    elif args:
        return "Usage: /roles   or   /roles <role> <light|normal|heavy>"
    return sub.roles.describe(sub.models)
