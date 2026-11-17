"""Bridges the older word-list (/entity) and code (/code) taxonomies into the universal one."""
from lily.memory.taxonomy import store
from lily.memory.taxonomy.paths import UNKNOWN, slug
from lily.utils.errors import LilyError

SOURCE = "auto:legacy"   # labels made here carry this source, so a rescan only replaces these


def target(mapping, cls, sub=""):
    """Where an old class goes: ('entity', 'animal') -> 'nature/animal'. Not mapped -> 'unknown/<class>'."""
    exact = mapping.get(f"{cls}/{sub}".lower())
    if exact:
        return exact
    base = mapping.get(cls.lower())
    if base is None:
        return f"{UNKNOWN}/{slug(cls)}"
    return f"{base}/{slug(sub)}" if slug(sub) else base


def label_run(tax, run_id):
    """Replace the automatic labels of one chat. Your own labels are never touched."""
    db, mapping, ref = tax.db, tax.tree.legacy, str(run_id)
    paths = {target(mapping, cls, sub) for cls, sub in
             db.rows("SELECT DISTINCT cls, sub FROM entity_mentions WHERE run_id = ?", (run_id,))}
    if "code" in mapping and db.rows("SELECT 1 FROM code_blocks WHERE run_id = ? LIMIT 1", (run_id,)):
        paths.add(mapping["code"])
    store.unlabel(db, "run", ref, source=SOURCE)
    for path in sorted(paths):
        try:
            tax.classify("run", ref, path, SOURCE, create=True)
        except LilyError:   # the mapped place is not usable (config edited?): keep it, as unknown
            tax.classify("run", ref, f"{UNKNOWN}/{path.split('/')[0]}", SOURCE)
    return len(paths)
