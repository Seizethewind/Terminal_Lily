"""Finds tools: built-in ones in lily/tools/builtin and your plugins/ folder.

One file = one tool: the file defines a class named `Tool` that extends
BaseTool. Files starting with an underscore are ignored.
"""
import importlib
import importlib.util
import pkgutil

from lily.tools import builtin
from lily.tools.base import BaseTool
from lily.utils.logger import get_logger
from lily.utils.paths import PLUGINS_DIR

log = get_logger("tools")


def _builtin_sources():
    for info in pkgutil.iter_modules(builtin.__path__):
        if not info.name.startswith("_"):
            name = f"lily.tools.builtin.{info.name}"
            yield f"builtin {info.name}", lambda name=name: importlib.import_module(name)


def _import_file(path):
    spec = importlib.util.spec_from_file_location(f"lily_plugin_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _plugin_sources(folder):
    files = sorted(folder.glob("*.py")) if folder.is_dir() else []
    for path in files:
        if not path.name.startswith("_"):
            yield f"plugin {path.name}", lambda path=path: _import_file(path)


def _make(module, lily):
    cls = getattr(module, "Tool", None)
    if not (isinstance(cls, type) and issubclass(cls, BaseTool)):
        raise TypeError("it must define a class named Tool that extends BaseTool")
    return cls(lily)


def load_all(lily, plugins_dir=PLUGINS_DIR):
    """Return (tools, errors). A broken tool never stops the others."""
    tools, errors = [], []
    for label, import_it in [*_builtin_sources(), *_plugin_sources(plugins_dir)]:
        try:
            tools.append(_make(import_it(), lily))
        except Exception as err:   # noqa: BLE001 - plugins are untrusted code
            log.warning("could not load %s: %s", label, err)
            errors.append(f"{label}: {err}")
    return tools, errors
