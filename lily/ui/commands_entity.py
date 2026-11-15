"""The /entity command: the taxonomy of things, subjects and computing."""
from lily.ui.commands import command, layer

USAGE = (
    "Usage: /entity | /entity classes | /entity show <class[/sub]> | /entity find <word> | "
    "/entity add <word> <class/sub> | /entity remove <word> | /entity scan"
)


def _split(words):
    """['blue', 'pen', 'object/tool'] -> ('blue pen', 'object/tool'). The label starts at the first
    part with a '/', so a subclass may contain spaces: ['stack', 'computing/data', 'structure']."""
    start = next((n for n, part in enumerate(words) if "/" in part), len(words) - 1)
    return " ".join(words[:start]), " ".join(words[start:])


@command("entity", "taxonomy of things: /entity, /entity add <word> <class/sub>, /entity find <word>")
def _entity(lily, args):
    entities = layer(lily, "memory").entities
    if not args:
        return entities.report()
    action, rest = args[0], args[1:]
    if action == "classes":
        return entities.classes()
    if action == "scan":
        return entities.scan()
    if action == "show" and rest:
        return entities.show(" ".join(rest))
    if action == "find" and rest:
        return entities.find(" ".join(rest))
    if action == "add" and len(rest) >= 2:
        return entities.add(*_split(rest))
    if action == "remove" and rest:
        return entities.remove(" ".join(rest))
    return USAGE
