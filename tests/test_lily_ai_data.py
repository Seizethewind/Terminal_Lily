import contextlib
import io
import random
import tempfile
import unittest
from pathlib import Path

from lily_ai import bpe_train, data, prepare
from lily_ai.tokenizer import END

TEXT = "Lily likes anime and games. The cat sat on the mat.\n" * 200


class DataTests(unittest.TestCase):
    def test_files_become_ids_with_an_end_marker_and_survive_saving(self):
        tok = bpe_train.train(TEXT, 300)
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "a.txt"
            source.write_text(TEXT, encoding="utf-8")
            ids = data.encode_files([source, source], tok)
            self.assertEqual(ids.count(END), 2)
            data.save(ids, Path(folder) / "x.bin")
            self.assertEqual(data.load(Path(folder) / "x.bin"), ids)

    def test_split_keeps_the_end_for_checking(self):
        ids = data.array("H", range(1000))
        train, check = data.split(ids, 0.1)
        self.assertEqual((len(train), len(check)), (900, 100))
        self.assertEqual(check[-1], 999)

    def test_batches_are_shifted_by_one_and_too_little_text_is_refused(self):
        ids = data.array("H", range(500))
        xs, ys = data.sample(ids, 4, 16, random.Random(1))
        self.assertEqual((len(xs), len(xs[0])), (4, 16))
        self.assertTrue(all(y[:-1] == x[1:] and y[-1] == x[-1] + 1 for x, y in zip(xs, ys)))
        with self.assertRaises(ValueError):
            data.sample(data.array("H", range(10)), 2, 16, random.Random(1))

    def test_prepare_builds_the_tokenizer_and_both_data_files(self):
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "notes.md").write_text(TEXT, encoding="utf-8")
            out = Path(folder) / "out"
            with contextlib.redirect_stdout(io.StringIO()):
                prepare.main([folder, "--vocab", "300", "--out", str(out)])
            self.assertEqual({p.name for p in out.iterdir()}, {"tokenizer.json", "train.bin", "val.bin"})
            self.assertGreater(len(data.load(out / "train.bin")), 100)


if __name__ == "__main__":
    unittest.main()
