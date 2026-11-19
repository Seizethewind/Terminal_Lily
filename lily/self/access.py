"""Lets the self tools reach the self layer, and say so plainly when it is off."""
from lily.utils.errors import ToolError


def of(lily):
    sub = lily.router.get("self")
    if sub is None:
        raise ToolError("Lily's self layer is off: check config/self.toml and .env (LILY_API_KEY)")
    return sub
