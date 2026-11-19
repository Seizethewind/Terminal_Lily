"""The /auto command: show or set how much Lily does without asking."""
from lily.ui.commands import command, layer
from lily.utils.errors import LilyError


@command("auto", "show or set autonomy: /auto none, basic, semi or full")
def _auto(lily, args):
    autonomy = getattr(layer(lily, "self"), "autonomy", None)
    if autonomy is None:
        raise LilyError("autonomy needs the self layer")
    if not args:
        return autonomy.describe()
    autonomy.set(args[0].lower())
    return autonomy.describe()
