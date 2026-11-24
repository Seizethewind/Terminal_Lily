import tempfile
import unittest
from pathlib import Path

from lily_ai import bpe_train, config
from lily_ai.tokenizer import END, FIRST, Tokenizer

TEXT = ("the cat sat on the mat. the cat ate the rat. a dog sat on the log, and the dog ate the cat's food.\n" * 30
        + "Lily likes anime and games. Lily likes games a lot!\n" * 30)


class SizeTests(unittest.TestCase):
    def test_the_parameter_counts_match_the_names(self):
        counts = {name: cfg.parameters() for name, (cfg, _) in config.SIZES.items()}
        self.assertEqual(counts["small"], 12_297_984)
        self.assertTrue(900_000 < counts["test"] < 1_000_000)
        self.assertTrue(27_000_000 < counts["medium"] < 28_000_000)

    def test_bad_sizes_are_refused(self):
        with self.assertRaises(ValueError):
            config.ModelConfig(1000, 100, 2, 3, 64)   # 100 does not divide by 3
        with self.assertRaises(ValueError):
            config.ModelConfig(40000, 128, 2, 4, 64)  # ids must fit in 15 bits


class TokenizerTests(unittest.TestCase):
    def setUp(self):
        self.tok = bpe_train.train(TEXT, 400)

    def test_it_learns_merges_and_keeps_ids_in_range(self):
        self.assertGreater(self.tok.size, FIRST)
        self.assertLessEqual(self.tok.size, 400)
        self.assertTrue(all(0 <= i < self.tok.size for i in self.tok.encode(TEXT)))

    def test_text_comes_back_exactly(self):
        for text in (TEXT, "new words, unseen: zebra!", "  spaces\n\nand\ttabs ", "naïve café 日本語 🙂", ""):
            self.assertEqual(self.tok.decode(self.tok.encode(text)), text)

    def test_common_text_gets_shorter_than_its_bytes(self):
        self.assertLess(len(self.tok.encode(TEXT)), len(TEXT.encode()) / 2)

    def test_training_is_repeatable_and_saves_and_loads(self):
        self.assertEqual(self.tok.merges, bpe_train.train(TEXT, 400).merges)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "t.json"
            self.tok.save(path)
            self.assertEqual(Tokenizer.load(path).encode(TEXT), self.tok.encode(TEXT))

    def test_it_stops_when_there_is_nothing_left_to_join(self):
        tiny = bpe_train.train("ab", 1000)
        self.assertEqual(tiny.size, FIRST + 1)
        self.assertEqual(tiny.pieces[END], b"")


if __name__ == "__main__":
    unittest.main()
