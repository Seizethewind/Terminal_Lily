"""The /code command: the coding taxonomy (languages seen in Lily's chats)."""
from lily.ui.commands import command, layer

USAGE = "Usage: /code | /code scan | /code show <language> [n] | /code export <language>"


@command("code", "coding taxonomy: /code, /code scan, /code show <lang>, /code export <lang>")
def _code(lily, args):
    code = layer(lily, "memory").code
    if not args:
        return code.report()
    action, rest = args[0], args[1:]
    if action == "scan":
        return code.scan()
    if action == "show" and rest:
        return code.show(rest[0], int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else 5)
    if action == "export" and rest:
        return code.export(rest[0], lily.settings.data_dir)
    return USAGE
