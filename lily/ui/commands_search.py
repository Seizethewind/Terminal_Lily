"""The /search command: look through chats, notes and your dictionary."""
from lily.memory.search import USAGE
from lily.ui.commands import command, layer


@command("search", "search chats, notes and your dictionary: /search <words> [in <path>] [only chats|notes|words]")
def _search(lily, args):
    engine = layer(lily, "memory").search
    if not args:
        return USAGE
    if args == ["more"]:
        return engine.more()
    if len(args) == 2 and args[0] == "chat" and args[1].isdigit():
        return engine.chat(int(args[1]))
    return engine.run(" ".join(args))
