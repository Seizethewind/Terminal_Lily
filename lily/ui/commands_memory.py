"""Slash commands for the data layer: feedback, lessons, history, dataset."""
from lily.ui.commands import command, layer


def _memory(lily):
    return layer(lily, "memory")


@command("good", "mark Lily's last answer as good, e.g. /good nice and short")
def _good(lily, args):
    return _memory(lily).rate(1, " ".join(args))


@command("bad", "mark Lily's last answer as bad, e.g. /bad wrong answer")
def _bad(lily, args):
    return _memory(lily).rate(-1, " ".join(args))


@command("lesson", "teach Lily something to remember, e.g. /lesson I like short answers")
def _lesson(lily, args):
    return _memory(lily).lesson(" ".join(args)) if args else "Usage: /lesson <what Lily should remember>"


@command("lessons", "list lessons and summaries")
def _lessons(lily, args):
    return _memory(lily).describe_lessons()


@command("unlearn", "remove a lesson by its number from /lessons")
def _unlearn(lily, args):
    if len(args) != 1 or not args[0].isdigit():
        return "Usage: /unlearn <number from /lessons>"
    return _memory(lily).unlearn(int(args[0]))


@command("history", "show recent exchanges, e.g. /history 5")
def _history(lily, args):
    return _memory(lily).history(int(args[0]) if args and args[0].isdigit() else 10)


@command("summarize", "summarize recent chats and keep the summary as a note")
def _summarize(lily, args):
    return _memory(lily).summarize()


@command("export", "write chats rated /good to data/dataset.jsonl (/export all = every chat)")
def _export(lily, args):
    return _memory(lily).export(only_good=args[:1] != ["all"])


@command("stats", "runs and verdicts per model profile")
def _stats(lily, args):
    return _memory(lily).stats()
