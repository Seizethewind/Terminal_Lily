"""One search over everything stored: chats, notes and your dictionary, optionally inside one category."""
from lily.memory import chat_search, dict_store, search_query
from lily.memory.taxonomy import store
from lily.utils.errors import LilyError

PAGE = 5   # results per kind and page
CLIP = 150
USAGE = "Usage: /search <words> [in <category path>] [only chats|notes|words] | /search more | /search chat <number>"


def _cut(text, size=CLIP):
    text = " ".join(str(text).split())
    return text if len(text) <= size else text[:size] + "..."


class Search:
    def __init__(self, get_db, taxonomy, get_rag):
        self._get_db, self.tax, self._get_rag, self.last = get_db, taxonomy, get_rag, None

    @property
    def db(self):
        return self._get_db()

    def run(self, text):
        query, path, kind = search_query.parse(text, self.tax.tree)
        if not search_query.words(query):
            raise LilyError(USAGE)
        self.last = (query, path, 0)
        parts = {"chats": lambda: self._chats(query, path, 0), "notes": lambda: self._notes(query, path),
                 "words": lambda: self._words(query, path)}
        found = [make() for name, make in parts.items() if kind in ("", name)]
        return "\n\n".join(part for part in found if part) or f"nothing found for '{query}'" + (
            f" in {path}" if path else "")

    def more(self):
        if self.last is None:
            raise LilyError("search for something first: /search <words>")
        query, path, offset = self.last
        text = self._chats(query, path, offset + PAGE)
        if not text:
            return "no more chats"
        self.last = (query, path, offset + PAGE)
        return text

    def _chats(self, query, path, offset):
        scope = store.run_filter(path, self.tax.tree.span(path)) if path else ("", ())
        rows, more = chat_search.find(self.db, query, scope, PAGE, offset)
        if not rows:
            return ""
        head = f"Chats {offset + 1}-{offset + len(rows)}" + ("  (/search more for the next ones)" if more else "")
        return "\n".join([head, *(f"  #{run}  {when}  {snippet}" for run, when, snippet in rows)])

    def _notes(self, query, path):
        rag = self._get_rag()
        if rag is None:
            return ""
        sources = {ref for _, ref in self.tax.refs([path], kind="note")} if path else None
        hits = rag.search(query, PAGE, sources=sources)
        return "Notes\n" + "\n".join("  " + _cut(hit) for hit in hits) if hits else ""

    def _words(self, query, path):
        wanted = search_query.words(query)
        items = dict_store.under(self.db, path) if path else dict_store.everything(self.db)
        found = [item for item in items
                 if all(word in " ".join([item["term"], *item["aliases"], item["meaning"].lower()]) for word in wanted)]
        return "Words\n" + "\n".join(f"  {i['label']}  - {_cut(i['meaning'])}" for i in found[:PAGE]) if found else ""

    def chat(self, number):
        rows = self.db.rows("SELECT ts, user_text, answer, error FROM runs WHERE id = ?", (number,))
        if not rows:
            raise LilyError(f"no chat #{number}")
        when, question, answer, error = rows[0]
        text = f"#{number}  {when[:16]}\nyou> {_cut(question, 1500)}\nlily> {_cut(answer, 1500)}"
        return text + (f"\nerror: {error}" if error else "") + "\nfiled as:\n" + self.tax.of("run", str(number))
