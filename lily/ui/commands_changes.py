"""Slash commands for staged files: /changes, /apply, /discard, /undo."""
from lily.ui.commands import command, layer
from lily.utils.errors import LilyError


def _staging(lily):
    staging = getattr(layer(lily, "self"), "staging", None)
    if staging is None:
        raise LilyError("staging is off: set enabled = true under [staging] in config/self.toml")
    return staging


@command("changes", "show files waiting to be saved, e.g. /changes or /changes notes.txt")
def _changes(lily, args):
    return _staging(lily).changes(" ".join(args) or None)


@command("apply", "save all waiting files (typing this is your yes)")
def _apply(lily, args):
    return _staging(lily).apply()


@command("discard", "drop waiting files, e.g. /discard or /discard notes.txt")
def _discard(lily, args):
    return _staging(lily).discard(" ".join(args) or None)


@command("undo", "put back the files the last /apply replaced")
def _undo(lily, args):
    return _staging(lily).undo()
