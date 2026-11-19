"""Decides what Lily may do without asking: looking is free, changing things asks."""
from pathlib import Path

from lily.tools import shell_risk, shell_safety
from lily.tools.secrets import is_secret
from lily.utils.paths import in_workplace

FREE = {"rag_search", "web_search", "task_status", "remember", "delegate", "show_changes", "discard_changes"}
SELF_ASKING = {"apply_changes", "undo_apply"}   # these show the file list and ask the user themselves
FREE_TERMUX = {"battery"}


def decide(name, args, staged=False, level="basic"):
    """'allow' (no question), 'write' (one question per folder and task) or 'ask' (every time).

    `staged` is True when writes only wait in the staging area, so writing needs no question.
    `level` is the autonomy level: none asks about every outside action, full also runs ordinary commands.
    """
    inside = name in FREE or name in SELF_ASKING   # Lily's own bookkeeping, never outside the app
    if level == "none" and not inside:
        return "ask"
    if inside:
        return "allow"
    if name == "read_file":
        return "ask" if is_secret(args.get("path", "")) else "allow"
    if name == "shell":
        command = args.get("command", "")
        if shell_safety.is_read_only(command) or (level == "full" and not shell_risk.is_risky(command)):
            return "allow"
        return "ask"
    if name == "termux_api":
        return "allow" if args.get("action") in FREE_TERMUX else "ask"
    if name == "write_file":
        if is_secret(args.get("path", "")):
            return "ask"
        return "allow" if staged else "write"
    return "ask"   # plugins, MCP tools, approve_task and anything new


def folder(args):
    """The folder a write_file call would change."""
    return in_workplace(args.get("path", ".")).parent


def covered(target, grants):
    """Was saving into `target` already allowed? A grant covers its subfolders, but never the home folder's."""
    home = Path.home()
    return any(
        grant == target or (grant in target.parents and grant != home and grant not in home.parents)
        for grant in grants
    )
