import subprocess
import unittest

from lily.utils.paths import CONFIG_DIR

ROOT = CONFIG_DIR.parent


class LocalAiSetupTests(unittest.TestCase):
    def test_modelfile_is_plain(self):
        text = (CONFIG_DIR / "local_ai" / "Modelfile").read_text(encoding="utf-8")
        self.assertIn("\nFROM gemma4:", text)
        self.assertIn("Lily_Ai 0.1", text)
        for odd in ("http", "curl", "TEMPLATE", "ADAPTER", "MESSAGE"):
            self.assertNotIn(odd, text)

    def test_script_has_valid_syntax_and_makes_the_model_lilys_fallback_expects(self):
        script = ROOT / "scripts" / "setup_local_ai.sh"
        self.assertEqual(subprocess.run(["bash", "-n", str(script)]).returncode, 0)
        self.assertIn('NAME="lily_ai:0.1"', script.read_text(encoding="utf-8"))

    def test_the_fallback_config_points_at_that_model(self):
        self.assertIn('model = "lily_ai:0.1"', (CONFIG_DIR / "self.toml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
