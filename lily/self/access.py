"""Lets the self tools reach the self layer, and say so plainly when it is off."""
from lily.utils.errors import ToolError


def _sub(lily):
    router = getattr(lily, "router", None)
    return router.get("self") if router is not None else None


def of(lily):
    sub = lily.router.get("self")
    if sub is None:
        raise ToolError("Lily's self layer is off: check config/self.toml and the key in .env")
    return sub


def staging(lily):
    """The staging area, or None when the self layer or staging is off (or `lily` is not a real Lily)."""
    return getattr(_sub(lily), "staging", None)


def need_staging(lily):
    found = staging(lily)
    if found is None:
        raise ToolError("staging is off: set enabled = true under [staging] in config/self.toml")
    return found


def level(lily):
    """The autonomy level: none, basic, semi or full. 'basic' when the self layer is off."""
    autonomy = getattr(_sub(lily), "autonomy", None)
    return autonomy.level if autonomy is not None else "basic"
