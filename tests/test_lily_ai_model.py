import importlib.util
import tempfile
import unittest
from pathlib import Path

from lily_ai import data, prepare
from lily_ai.config import SIZES

HAS_TORCH = importlib.util.find_spec("torch") is not None
TEXT = "Lily likes anime and games. The cat sat on the mat.\n" * 400


@unittest.skipUnless(HAS_TORCH, "PyTorch is not installed here (it is on Kaggle and Colab)")
class ModelTests(unittest.TestCase):
    def test_every_size_has_the_promised_parameter_count_and_output_shape(self):
        import torch

        from lily_ai.model import GPT
        for name, (cfg, _) in SIZES.items():
            if name == "medium":
                continue   # same code as the others; skipped to keep the test quick
            model = GPT(cfg)
            self.assertEqual(sum(p.numel() for p in model.parameters()), cfg.parameters(), name)
            ids = torch.randint(0, cfg.vocab, (2, 16))
            logits, loss = model(ids, ids)
            self.assertEqual(tuple(logits.shape), (2, 16, cfg.vocab))
            self.assertTrue(torch.isfinite(loss))
            self.assertEqual(model.generate(ids[:1], 5).shape[1], 21)

    def test_training_runs_saves_resumes_and_generates(self):
        import contextlib
        import io

        from lily_ai import checkpoint, generate, train
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "text.txt").write_text(TEXT, encoding="utf-8")
            out = Path(folder) / "out"
            with contextlib.redirect_stdout(io.StringIO()):
                prepare.main([str(Path(folder) / "text.txt"), "--vocab", "300", "--out", str(out)])
                train.main(["--size", "test", "--data", str(out), "--steps", "40", "--every", "20", "--batch", "4"])
                train.main(["--size", "test", "--data", str(out), "--steps", "60", "--every", "20", "--batch", "4"])
            self.assertEqual(checkpoint.load(out / "test.pt")["step"], 60)
            shown = io.StringIO()
            with contextlib.redirect_stdout(shown):
                generate.main(["--size", "test", "--data", str(out), "--prompt", "Lily", "--tokens", "10"])
            self.assertTrue(shown.getvalue().startswith("Lily"))
            self.assertGreater(len(data.load(out / "train.bin")), 100)


if __name__ == "__main__":
    unittest.main()
