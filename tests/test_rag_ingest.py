import tempfile
import unittest
from pathlib import Path

from lily.rag import loader
from lily.rag.ingest import ingest
from lily.rag.store import Store
from lily.utils.errors import LilyError


def folder(files):
    root = Path(tempfile.mkdtemp())
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())
    return root


class IngestTests(unittest.TestCase):
    def test_folder_is_indexed_recursively(self):
        root = folder({"a.md": "alpha note", "sub/b.txt": "beta note", "image.png": "skip me"})
        store = Store(":memory:")
        self.assertEqual(ingest(store, root), (2, 2))
        self.assertEqual(len(store.search('"beta"', 5)), 1)

    def test_hidden_folders_and_binary_files_are_skipped(self):
        root = folder({".git/config": "secret", "bin.dat": b"a\x00b", "bin": b"x\x00y", "ok.md": "fine"})
        store = Store(":memory:")
        self.assertEqual(ingest(store, root)[0], 1)

    def test_single_file_and_reindexing_does_not_duplicate(self):
        root = folder({"a.md": "first version"})
        store = Store(":memory:")
        ingest(store, root / "a.md")
        (root / "a.md").write_text("second version", encoding="utf-8")
        ingest(store, root / "a.md")
        self.assertEqual(store.search('"first"', 5), [])
        self.assertEqual(len(store.search('"second"', 5)), 1)

    def test_oversized_files_are_skipped(self):
        root = folder({"big.txt": "x" * (loader.MAX_BYTES + 1), "small.txt": "ok"})
        self.assertEqual(ingest(Store(":memory:"), root)[0], 1)

    def test_missing_path_is_an_error(self):
        with self.assertRaisesRegex(LilyError, "not a file or folder"):
            ingest(Store(":memory:"), "/nonexistent/folder")


if __name__ == "__main__":
    unittest.main()
