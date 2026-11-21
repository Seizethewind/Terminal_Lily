"""Slash commands for the self layer: tasks, summary, roles, facts and phone notifications."""
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


@command("facts", "list what Lily remembers about you; /unremember <number> removes one")
def _facts(lily, args):
    rows = layer(lily, "self").memory.numbered_facts()
    return "\n".join(f"#{number} {text}" for number, text in rows) or "Nothing saved yet. Tell Lily, or use /remember."


@command("remember", "save a lasting fact about you, e.g. /remember I like tea")
def _remember(lily, args):
    if not args:
        return "Usage: /remember <something Lily should always know about you>"
    return layer(lily, "self").remember(" ".join(args))


@command("unremember", "remove one fact by its number from /facts")
def _unremember(lily, args):
    number = args[0].lstrip("#") if args else ""
    if not number.isdigit():
        return "Usage: /unremember <number from /facts>"
    return "Removed." if layer(lily, "self").memory.forget_fact(int(number)) else f"There is no fact #{number}."


@command("notify", "phone notifications for slow or failed tasks; /notify test sends one")
def _notify(lily, args):
    notifier = layer(lily, "self").notifier
    if not notifier.enabled:
        return ("Notifications are off: Termux:API was not found, or [notify] enabled = false in config/self.toml. "
                "Install the Termux:API app, run: pkg install termux-api, then restart Lily.")
    if args[:1] == ["test"]:
        notifier.send("Lily", "Notifications work.")
        return "Sent. Look at your notifications."
    return (f"Notifications are on: you get one when a task takes over {notifier.after} seconds or fails, "
            "and when a worker needs your OK. /notify test tries one.")
