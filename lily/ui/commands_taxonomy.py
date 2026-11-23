"""The /taxonomy command: the universal data taxonomy (organize and filter what Lily stored)."""
from lily.memory.taxonomy import browse
from lily.ui.commands import command, layer

USAGE = """Usage:
/taxonomy                              the tree with record counts
/taxonomy about <path>                 what a category means and what is inside it
/taxonomy find <word>                  where a word belongs in the tree
/taxonomy add <path> [description]     new subcategory, e.g. study/history
/taxonomy remove <path>                remove a subcategory you added (it must be empty)
/taxonomy label <kind> <path> <ref>    file a record, e.g. note study/history /sd/ww2.md
/taxonomy unlabel <kind> <path|all> <ref>
/taxonomy of <kind> <ref>              the labels of one record
/taxonomy show [all] <path> [path...]  records filed there (all = in every path)
/taxonomy unclassified [kind]          records with no label yet (default: run)
/taxonomy search <path> <question>     search only the notes filed there
/taxonomy scan                         redo the automatic labels of every chat (also after editing config/taxonomy_auto.toml)
kinds: run (ref = chat number), note (ref = source shown by /notes)"""


SHOWN = 50   # lines printed at most; a long list is cut with a count


def _more(total, shown, hint=""):
    return f"\n... and {total - shown} more{hint}" if total > shown else ""


def _lines(refs):
    text = "\n".join(f"{kind} {ref}" for kind, ref in refs[:SHOWN]) or "nothing filed there"
    return text + _more(len(refs), SHOWN, ". Narrow it with a deeper path, or search: /search <words> in <path>")


@command("taxonomy", "organize stored data: /taxonomy, /taxonomy add|label|show|search ...")
def _taxonomy(lily, args):
    tax = layer(lily, "memory").taxonomy
    action, rest = (args[0], args[1:]) if args else ("", [])
    if action == "":
        return tax.report()
    if action == "scan":
        return tax.scan()
    if action == "about" and rest:
        return browse.about(tax.tree, tax.db, rest[0])
    if action == "find" and rest:
        return browse.find(tax.tree, " ".join(rest))
    if action == "add" and rest:
        return tax.add(rest[0], " ".join(rest[1:]))
    if action == "remove" and rest:
        return tax.remove(rest[0])
    if action == "label" and len(rest) >= 3:
        return tax.classify(rest[0], " ".join(rest[2:]), rest[1])
    if action == "unlabel" and len(rest) >= 3:
        return tax.unclassify(rest[0], " ".join(rest[2:]), None if rest[1] == "all" else rest[1])
    if action == "of" and len(rest) >= 2:
        return tax.of(rest[0], " ".join(rest[1:]))
    if action == "show" and rest:
        mode, paths = ("all", rest[1:]) if rest[0] == "all" else ("any", rest)
        return _lines(tax.refs(paths, mode=mode))
    if action == "unclassified":
        kind = rest[0] if rest else "run"
        rows = tax.unclassified(kind, SHOWN)
        text = "\n".join(f"{ref}  {text}".rstrip() for ref, text in rows) or "nothing is unclassified"
        return text + _more(tax.unclassified_count(kind), len(rows))
    if action == "search" and len(rest) >= 2:
        sources = {ref for _, ref in tax.refs([rest[0]], kind="note")}
        hits = layer(lily, "rag").search(" ".join(rest[1:]), 5, sources=sources)
        return "\n---\n".join(hits) or f"no matching notes filed under {rest[0]}"
    return USAGE
