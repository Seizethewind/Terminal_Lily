import json
import tempfile
import unittest
from pathlib import Path

from lily.memory import run_log
from lily.memory.code_taxonomy import CodeTaxonomy
from lily.memory.db import Database
from lily.ui import commands
from lily.utils.errors import LilyError
from tests.fakes import text_reply
from tests.memory_helpers import setup

PY = "Here:\n```python\nprint('hi')\n```\n"
WEIRD = "```brainfuck\n+++.\n```\n"


def taxonomy():
    db = Database(":memory:")
    return db, CodeTaxonomy(lambda: db)


class CodeTaxonomyTests(unittest.TestCase):
    def test_report_builds_the_tree_and_flags_unknown_languages(self):
        db, tax = taxonomy()
        tax.index_run(run_log.record(db, {"user_text": "", "answer": PY + PY}), "", PY + PY)
        tax.index_run(run_log.record(db, {}), "", WEIRD)
        lines = tax.report().splitlines()
        self.assertIn("2 block(s) in   1 chat(s)  programming > scripting > python", lines[0])
        self.assertIn("unknown > brainfuck   <- not in config/languages.toml", lines[1])

    def test_empty_report_explains_what_to_do(self):
        self.assertIn("no code blocks yet", taxonomy()[1].report())

    def test_indexing_a_chat_twice_does_not_duplicate(self):
        db, tax = taxonomy()
        run = run_log.record(db, {"user_text": "q", "answer": PY})
        tax.index_run(run, "q", PY)
        tax.index_run(run, "q", PY)
        self.assertEqual(db.rows("SELECT count(*) FROM code_blocks"), [(1,)])

    def test_scan_files_old_chats(self):
        db, tax = taxonomy()
        run_log.record(db, {"user_text": "q", "answer": PY})
        run_log.record(db, {"user_text": "q", "answer": "no code"})
        self.assertEqual(tax.scan(), "scanned 2 chat(s), found 1 code block(s)")
        self.assertEqual(db.rows("SELECT language FROM code_blocks"), [("python",)])

    def test_show_accepts_aliases(self):
        db, tax = taxonomy()
        run = run_log.record(db, {"user_text": "q", "answer": PY})
        tax.index_run(run, "q", PY)
        self.assertEqual(tax.show("py"), "chat #1 (answer, 1 line(s)): print('hi')")
        self.assertIn("no rust code", tax.show("rust"))
        with self.assertRaises(LilyError):
            tax.show("text")

    def test_export_writes_the_chats_of_one_language(self):
        db, tax = taxonomy()
        for answer in (PY, WEIRD):
            tax.index_run(run_log.record(db, {"user_text": "q", "answer": answer}), "q", answer)
        folder = Path(tempfile.mkdtemp())
        self.assertIn("wrote 1 chat(s)", tax.export("python", folder))
        row = json.loads((folder / "code_python.jsonl").read_text(encoding="utf-8"))
        self.assertEqual((row["language"], row["messages"][1]["content"]), ("python", PY))


class CodeFlowTests(unittest.TestCase):
    def test_every_answer_is_filed_as_it_happens(self):
        lily, memory = setup(text_reply(PY), text_reply(WEIRD))
        lily.handle("write python")
        lily.handle("write something odd")
        languages = [row[0] for row in memory.db.rows("SELECT language FROM code_blocks ORDER BY id")]
        self.assertEqual(languages, ["python", "brainfuck"])

    def test_code_pasted_by_the_user_is_filed_too(self):
        lily, memory = setup(text_reply("looks fine"))
        lily.handle("review this:\n```rust\nfn main() {}\n```")
        self.assertEqual(memory.db.rows("SELECT language, source FROM code_blocks"), [("rust", "question")])

    def test_slash_commands(self):
        lily, _ = setup(text_reply(PY))
        lily.handle("write python")
        self.assertIn("programming > scripting > python", commands.run(lily, "/code"))
        self.assertIn("chat #1", commands.run(lily, "/code show python"))
        self.assertIn("scanned 1 chat(s)", commands.run(lily, "/code scan"))
        self.assertIn("wrote 1 chat(s)", commands.run(lily, "/code export python"))
        self.assertTrue((lily.settings.data_dir / "code_python.jsonl").is_file())
        self.assertIn("Usage", commands.run(lily, "/code nonsense"))
        self.assertIn("Usage", commands.run(lily, "/code show"))


if __name__ == "__main__":
    unittest.main()
