"""The coding taxonomy: which languages show up in your chats, filed as group > family > language."""
import json
from pathlib import Path

from lily.memory import code_store
from lily.memory.code_extract import extract
from lily.memory.languages import Languages
from lily.utils.errors import LilyError


class CodeTaxonomy:
    def __init__(self, get_db, languages=None):
        self._get_db = get_db
        self._languages = languages

    @property
    def languages(self):
        if self._languages is None:
            self._languages = Languages()
        return self._languages

    def index_run(self, run_id, user_text, answer):
        """File the code blocks of one chat. Returns how many were found."""
        blocks = extract(user_text, self.languages, "question") + extract(answer, self.languages, "answer")
        code_store.save(self._get_db(), run_id, blocks)
        return len(blocks)

    def scan(self):
        """Re-file every stored chat (use after editing config/languages.toml)."""
        self._languages = Languages()
        runs = self._get_db().rows("SELECT id, user_text, answer FROM runs ORDER BY id")
        total = sum(self.index_run(*run) for run in runs)
        return f"scanned {len(runs)} chat(s), found {total} code block(s)"

    def report(self):
        rows = code_store.summary(self._get_db())
        if not rows:
            return "no code blocks yet. Ask Lily for some code, or run /code scan"
        lines = []
        for language, group, family, known, blocks, chats in rows:
            path = " > ".join(part for part in (group, family, language) if part)
            note = "" if known else "   <- not in config/languages.toml"
            lines.append(f"{blocks:>4} block(s) in {chats:>3} chat(s)  {path}{note}")
        return "\n".join(lines)

    def _name(self, text):
        info = self.languages.resolve(text)
        if info is None:
            raise LilyError(f"'{text}' is not a language name")
        return info["language"]

    def show(self, text, limit=5):
        name = self._name(text)
        rows = code_store.recent(self._get_db(), name, limit)
        if not rows:
            return f"no {name} code stored yet"
        first = lambda code: (code.strip().splitlines() or [""])[0][:70]   # noqa: E731
        return "\n".join(f"chat #{run} ({source}, {n} line(s)): {first(code)}" for run, source, n, code in rows)

    def export(self, text, folder):
        """Write the chats that contain a language to <folder>/code_<language>.jsonl."""
        name = self._name(text)
        chats = code_store.chats_with(self._get_db(), name)
        path = Path(folder) / f"code_{name}.jsonl"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as out:
                for question, answer in chats:
                    messages = [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
                    out.write(json.dumps({"language": name, "messages": messages}, ensure_ascii=False) + "\n")
        except OSError as err:
            raise LilyError(f"cannot write {path}: {err}") from err
        return f"wrote {len(chats)} chat(s) to {path}"
