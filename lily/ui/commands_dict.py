"""The /dict command: your own dictionary, tied to the taxonomy."""
from lily.ui.commands import command, layer

USAGE = """Usage:
/dict add <word> = <meaning> [@ <path>]   save a word, e.g. /dict add Naruto = ninja manga by Masashi Kishimoto @ study/entertainment/anime/anime-demographic/shonen
/dict alias <word> = <other>, <other>     other names for it
/dict <word>                              what it means
/dict find <text>                         words whose name or meaning mention it
/dict under <path>                        words filed under a category
/dict remove <word>
/dict load                                add the starter words from config/dictionary.toml"""


def _meaning_path(text):
    head, sep, tail = text.rpartition(" @ ")
    return (head.strip(), tail.strip()) if sep and " " not in tail.strip() else (text.strip(), "")


@command("dict", "your own dictionary: /dict add <word> = <meaning>, /dict <word>, /dict find <text>")
def _dict(lily, args):
    book = layer(lily, "memory").dictionary
    if not args:
        return f"{book.describe()}\n{USAGE}"
    action, rest = args[0], " ".join(args[1:])
    left, sep, right = rest.partition("=")
    if action == "add" and sep:
        return book.add(left, *_meaning_path(right))
    if action == "alias" and sep:
        return book.alias(left, right)
    if action in ("find", "under", "remove") and rest:
        return getattr(book, action)(rest)
    if action == "load":
        return book.load()
    return USAGE if action in ("add", "alias", "find", "under", "remove") else book.show(" ".join(args))
