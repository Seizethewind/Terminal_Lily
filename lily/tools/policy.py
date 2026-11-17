"""Decides what Lily may do without asking: looking is free, changing things asks."""
from pathlib import Path

from lily.tools import shell_safety
from lily.tools.secrets import is_secret

FREE = {"rag_search", "web_search", "task_status", "remember", "delegate"}
FREE_TERMUX = {"battery"}


def decide(name, args):
    """'allow' (no question), 'write' (one question per folder and task) or 'ask' (every time)."""
    if name in FREE:
        return "allow"
    if name == "read_file":
        return "ask" if is_secret(args.get("path", "")) else "allow"
    if name == "shell":
        return "allow" if shell_safety.is_read_only(args.get("command", "")) else "ask"
    if name == "termux_api":
        return "allow" if args.get("action") in FREE_TERMUX else "ask"
    if name == "write_file":
        return "ask" if is_secret(args.get("path", "")) else "write"
    return "ask"   # plugins, MCP tools, approve_task and anything new


def folder(args):
    """The folder a write_file call would change."""
    return Path(str(args.get("path", "."))).expanduser().resolve().parent


def covered(target, grants):
    """Was saving into `target` already allowed? A grant covers its subfolders, but never the home folder's."""
    home = Path.home()
    return any(
        grant == target or (grant in target.parents and grant != home and grant not in home.parents)
        for grant in grants
    )
