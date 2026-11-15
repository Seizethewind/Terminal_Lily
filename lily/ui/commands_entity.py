"""The /entity command: the entity taxonomy (entity, location, object)."""
from lily.ui.commands import command, layer

USAGE = (
    "Usage: /entity | /entity classes | /entity show <class[/sub]> | /entity find <word> | "
    "/entity add <word> <class/sub> | /entity remove <word> | /entity scan"
)


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
        return entities.show(rest[0])
    if action == "find" and rest:
        return entities.find(" ".join(rest))
    if action == "add" and len(rest) >= 2:
        return entities.add(" ".join(rest[:-1]), rest[-1])
    if action == "remove" and rest:
        return entities.remove(" ".join(rest))
    return USAGE
