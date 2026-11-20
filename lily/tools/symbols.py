"""A short map of the files and functions in a folder, so the right file can be found without reading them all."""
import ast
import os
import re
from pathlib import Path

from lily.tools import tidy
from lily.tools.secrets import is_secret

SKIP = {"node_modules", "__pycache__", "venv", "build", "dist", "target"}   # folders starting with a dot too
CODE = {".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".swift", ".c", ".h", ".cpp"}
KNOWN = CODE | {".py", ".md"}
MAX_FILES, MAX_BYTES, MAX_SYMBOLS = 400, 200_000, 40
DEF = re.compile(
    r"^\s*(?:(?:export|pub|public|private|protected|static|async|final|default)\s+)*"
    r"(function|class|def|fn|func|interface|struct|enum|trait|fun|object)\s+([A-Za-z_]\w*)"
)
HEADING = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _generic(text):
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        match = DEF.match(line)
        if match:
            found.append((number, f"{match.group(1)} {match.group(2)}"))
    return found


def _python(text):
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return _generic(text)
    found = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            found.append((node.lineno, f"class {node.name}"))
            found += [(m.lineno, f"  {node.name}.{m.name}") for m in node.body if isinstance(m, FUNCS)]
        elif isinstance(node, FUNCS):
            found.append((node.lineno, f"def {node.name}"))
    return found


def _markdown(text):
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        match = HEADING.match(line)
        if match:
            found.append((number, f"{match.group(1)} {match.group(2)[:60]}"))
    return found


def file_symbols(path, text):
    """[(line number, label)] for one file."""
    suffix = Path(path).suffix.lower()
    if suffix == ".py":
        return _python(text)
    return _markdown(text) if suffix == ".md" else _generic(text)


def _walk(root):
    for folder, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if not d.startswith(".") and d not in SKIP)
        for name in sorted(names):
            path = Path(folder) / name
            try:
                ok = path.suffix.lower() in KNOWN and not is_secret(name) and path.stat().st_size <= MAX_BYTES
            except OSError:
                continue
            if ok:
                yield path


def build_map(root, query="", budget=6000):
    """Files with their classes and functions. `query` keeps only matching files or symbols."""
    root, query = Path(root), query.strip().lower()
    blocks, used, omitted, seen = [], 0, 0, 0
    for path in _walk(root):
        seen += 1
        if seen > MAX_FILES:
            omitted += 1
            break
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(path.relative_to(root))
        found = file_symbols(path, text)[:MAX_SYMBOLS]
        if query and query not in rel.lower():
            found = [item for item in found if query in item[1].lower()]
            if not found:
                continue
        block = [f"{rel} ({text.count(chr(10)) + 1} lines)"] + [f"  L{n} {label}" for n, label in found]
        size = sum(len(line) + 1 for line in block)
        if used + size > budget:
            omitted += 1
            continue
        blocks.append("\n".join(block))
        used += size
    if not blocks and not omitted:
        return f"No source files found in {tidy.short(root)}" + (f" for '{query}'." if query else ".")
    lines = [f"Code map of {tidy.short(root)}: {len(blocks)} file(s) shown.", *blocks]
    if omitted:
        lines.append(f"[{omitted} more file(s) not shown: narrow it with find, or give a sub-folder]")
    return "\n".join(lines)
