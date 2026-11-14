import tempfile
import unittest
from pathlib import Path

from config.settings import Settings
from lily.orchestrator import Lily
from lily.utils.errors import ConfigError, LilyError

MODELS = 'default = "auto"\n[profiles]\nauto = "auto"\nfast = "auto:fast"\n'


def load_from(models_text):
    folder = Path(tempfile.mkdtemp())
    if models_text is not None:
        (folder / "models.toml").write_text(models_text, encoding="utf-8")
    (folder / "system_prompt.txt").write_text("hello", encoding="utf-8")
    return Settings.load(folder)


class SettingsTests(unittest.TestCase):
    def test_loads_profiles_and_prompt(self):
        settings = load_from(MODELS)
        self.assertEqual(settings.profiles["fast"], "auto:fast")
        self.assertEqual(settings.system_prompt, "hello")
        self.assertEqual(settings.profile, "auto")

    def test_missing_models_file(self):
        with self.assertRaises(ConfigError):
            load_from(None)

    def test_default_must_exist(self):
        with self.assertRaises(ConfigError):
            load_from('default = "nope"\n[profiles]\nauto = "auto"\n')

    def test_bad_toml(self):
        with self.assertRaises(ConfigError):
            load_from("this is = = not toml")

    def test_profile_switching_on_main_orchestrator(self):
        lily = Lily(load_from(MODELS))
        lily.set_profile("fast")
        self.assertEqual(lily.model, "auto:fast")
        with self.assertRaises(LilyError):
            lily.set_profile("turbo")


if __name__ == "__main__":
    unittest.main()
