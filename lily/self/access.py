"""Lets the self tools reach the self layer, and say so plainly when it is off."""
from lily.utils.errors import ToolError


def of(lily):
    sub = lily.router.get("self")
    if sub is None:
        raise ToolError("Lily's self layer is off: check config/self.toml and the key in .env")
    return sub


def staging(lily):
    """The staging area, or None when the self layer or staging is off (or `lily` is not a real Lily)."""
    router = getattr(lily, "router", None)
    sub = router.get("self") if router is not None else None
    return getattr(sub, "staging", None)


def need_staging(lily):
    found = staging(lily)
    if found is None:
        raise ToolError("staging is off: set enabled = true under [staging] in config/self.toml")
    return found
