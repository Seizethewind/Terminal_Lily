"""Plain-English wording for the 'allow?' question, so you never read raw JSON."""
LIMIT = 400   # characters of any one detail that are shown

FIXED = {   # tool name -> (what Lily wants to do, the argument that says what exactly)
    "shell": ("run a command on your phone", "command"),
    "read_file": ("read a file", "path"),
    "web_search": ("search the web", "query"),
    "rag_search": ("look through her saved notes", "query"),
}
TERMUX = {
    "battery": "check your battery", "clipboard_get": "read your clipboard",
    "clipboard_set": "copy text to your clipboard", "notify": "show a notification",
    "toast": "show a short message on screen",
}


def _cut(value):
    text = str(value)
    return text if len(text) <= LIMIT else f"{text[:LIMIT]}... ({len(text) - LIMIT} more characters)"


def describe(name, args):
    """Return (what Lily wants to do, [detail lines])."""
    if name in FIXED:
        what, key = FIXED[name]
        return what, [_cut(args[key])] if key in args else []
    if name == "write_file":
        what = "add text to the end of a file" if args.get("append") else "write to a file"
        size = len(str(args.get("content", "")))
        return what, [_cut(args.get("path", "?")), f"({size} characters of text)"]
    if name == "termux_api":
        details = [_cut(args[key]) for key in ("title", "text") if args.get(key)]
        return TERMUX.get(args.get("action"), "use your phone"), details
    return f"use the tool '{name}'", [f"{key}: {_cut(value)}" for key, value in args.items()]
