"""Builds Lily and plugs in whichever sub orchestrators exist."""
import importlib

from lily.orchestrator import Lily

SUBS = ("lily.llm.orchestrator", "lily.tools.orchestrator", "lily.rag.orchestrator")


def build(settings):
    lily = Lily(settings)
    for module in SUBS:
        try:
            mod = importlib.import_module(module)
        except ModuleNotFoundError as err:
            # Skip a layer that is not written yet, but not a missing dependency.
            if module == err.name or module.startswith(f"{err.name}."):
                continue
            raise
        mod.register(lily)
    return lily
