"""Slash commands. Each command is a small function registered by name."""
from lily.utils.errors import LilyError

EXIT = "__exit__"
COMMANDS = {}


def command(name, help_text):
    def decorate(fn):
        COMMANDS[name] = (fn, help_text)
        return fn
    return decorate


@command("help", "show this list")
def _help(lily, args):
    return "\n".join(f"/{name:<10}{info}" for name, (_, info) in sorted(COMMANDS.items()))


@command("clear", "forget this conversation")
def _clear(lily, args):
    lily.reset()
    return "Conversation cleared."


@command("profile", "show or set the model profile, e.g. /profile fast")
def _profile(lily, args):
    if not args:
        options = ", ".join(lily.settings.profiles)
        return f"profile: {lily.state.profile} ({lily.model}). Options: {options}"
    lily.set_profile(args[0])
    return f"profile set to {args[0]} ({lily.model})"


def layer(lily, name):
    sub = lily.router.get(name)
    if sub is None:
        raise LilyError(f"the {name} layer is not installed")
    return sub


@command("tools", "list loaded tools and any that failed to load")
def _tools(lily, args):
    return layer(lily, "tools").describe()


@command("reload", "reload plugins and MCP servers")
def _reload(lily, args):
    return layer(lily, "tools").reload()


@command("ingest", "add a file or folder to Lily's notes, e.g. /ingest ~/notes")
def _ingest(lily, args):
    if not args:
        return "Usage: /ingest <file or folder>"
    return layer(lily, "rag").ingest(" ".join(args))


@command("notes", "list what is in Lily's notes")
def _notes(lily, args):
    return layer(lily, "rag").describe()


@command("forget", "remove one source from the notes, e.g. /forget /path/file.md")
def _forget(lily, args):
    if not args:
        return "Usage: /forget <source as shown by /notes>"
    return layer(lily, "rag").forget(" ".join(args))


@command("exit", "leave Lily")
def _exit(lily, args):
    return EXIT


def run(lily, line):
    """Run a '/command arg ...' line and return its text (or EXIT)."""
    parts = line[1:].split()
    if not parts:
        return "Type /help to see the commands."
    name, args = parts[0], parts[1:]
    if name not in COMMANDS:
        return f"Unknown command /{name}. Try /help."
    return COMMANDS[name][0](lily, args)


from lily.ui import commands_changes, commands_code, commands_entity, commands_memory, commands_taxonomy  # noqa: E402,F401
