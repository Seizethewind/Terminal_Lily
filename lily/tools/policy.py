"""Decides what Lily may do without asking: looking inside the workplace is free, changing things asks."""
from pathlib import Path

from lily.tools import shell_risk, shell_safety
from lily.tools.secrets import is_secret
from lily.utils.paths import in_workplace

BOOKKEEPING = {"task_status", "remember", "delegate", "retry_task", "show_changes", "discard_changes"}   # Lily's own
SELF_ASKING = {"apply_changes", "undo_apply"}   # these show the file list and ask the user themselves
LOOKUP = {"rag_search", "web_search", "code_map"}
WRITES = {"write_file", "edit_file"}
FREE_TERMUX = {"battery"}
QUERY_MAX = 200   # shortcut: only long queries ask, a short one can still leak a little; ask on every search to close it


def decide(name, args, staged=False, level="basic"):
    """'allow' (no question), 'write' (one question per folder and task) or 'ask' (every time).

    `staged` is True when writes only wait in the staging area, so writing needs no question.
    `level` is the autonomy level: none asks about every outside action, full also runs ordinary commands.
    Reading a file or running a read-only command is quiet only inside the workplace and never for secrets.
    """
    if name in BOOKKEEPING or name in SELF_ASKING:
        return "allow"
    if level == "none":
        return "ask"
    if name == "web_search" and len(str(args.get("query", ""))) > QUERY_MAX:
        return "ask"   # a long query is a way to carry a file out
    if name in LOOKUP:
        return "allow"
    if name == "read_file":
        path = args.get("path", "")
        return "ask" if is_secret(path) or shell_risk.outside(path) else "allow"
    if name == "shell":
        command = args.get("command", "")
        looks = shell_safety.is_read_only(command) and not shell_risk.reaches_outside(command)
        if looks or (level == "full" and not shell_risk.is_risky(command)):
            return "allow"
        return "ask"
    if name == "termux_api":
        return "allow" if args.get("action") in FREE_TERMUX else "ask"
    if name in WRITES:
        path = args.get("path", "")
        if is_secret(path) or (level == "full" and shell_risk.outside(path)):
            return "ask"
        return "allow" if staged or level == "full" else "write"   # full: writes in the workplace go quietly
    return "ask"   # plugins, MCP tools, approve_task and anything new


def folder(args):
    """The folder a write_file or edit_file call would change."""
    return in_workplace(args.get("path", ".")).parent


def covered(target, grants):
    """Was saving into `target` already allowed? A grant covers its subfolders, but never the home folder's."""
    home = Path.home()
    return any(
        grant == target or (grant in target.parents and grant != home and grant not in home.parents)
        for grant in grants
    )
