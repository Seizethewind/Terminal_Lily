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


def _tools_layer(lily):
    tools = lily.router.get("tools")
    if tools is None:
        raise LilyError("the tools layer is not installed")
    return tools


@command("tools", "list loaded tools and any that failed to load")
def _tools(lily, args):
    return _tools_layer(lily).describe()


@command("reload", "reload plugins and MCP servers")
def _reload(lily, args):
    return _tools_layer(lily).reload()


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
