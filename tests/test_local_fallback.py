import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from lily.llm.base import Reply
from lily.llm.providers.openai_compat import OpenAICompat
from lily.self.config import SelfConfig
from lily.self.ollama import LocalProvider
from lily.self.router import ModelRouter
from lily.utils.errors import LLMError
from tests.fakes import FakeProvider, text_reply

DATA = {"workers": {"url": "https://r/v1", "key_env": "LILY_API_KEY"},
        "local": {"url": "http://127.0.0.1:11434/v1", "model": "Lily_Local", "timeout": 180}}


class _Down:
    def chat(self, payload):
        raise LLMError("no internet")


def config(**env):
    with mock.patch.dict(os.environ, env), mock.patch("lily.self.config.shutil.which", return_value="/bin/ollama"):
        return SelfConfig(DATA)


class ConfigTests(unittest.TestCase):
    def test_both_routers_are_on_by_default(self):
        self.assertEqual(set(config().endpoints), {"workers", "local"})

    def test_flags_turn_each_one_off(self):
        self.assertEqual(set(config(LILY_LOCAL="false").endpoints), {"workers"})
        self.assertEqual(set(config(LILY_ROUTER="false").endpoints), {"local"})

    def test_local_is_off_when_ollama_is_not_installed(self):
        with mock.patch("lily.self.config.shutil.which", return_value=None):
            self.assertEqual(set(SelfConfig(DATA).endpoints), {"workers"})


class FallbackOrderTests(unittest.TestCase):
    def router(self, workers, local):
        return ModelRouter(config(), {"workers": workers, "local": local}, clock=lambda: 0.0)

    def test_local_answers_only_when_the_router_fails(self):
        local = FakeProvider(text_reply("offline"))
        down = self.router(_Down(), local).chat("lily", None, [], model="auto")
        self.assertEqual(down.data["choices"][0]["message"]["content"], "offline")
        self.assertEqual(local.payloads[0]["model"], "Lily_Local")   # its own model name
        local, workers = FakeProvider(text_reply("offline")), FakeProvider(text_reply("online"))
        self.router(workers, local).chat("worker", "normal", [])
        self.assertEqual((local.payloads, workers.payloads[0]["model"]), ([], "auto"))

    def test_both_down_reports_both(self):
        with self.assertRaisesRegex(LLMError, "workers: no internet; local: no internet"):
            self.router(_Down(), _Down()).chat("lily", None, [], model="auto")


class LocalProviderTests(unittest.TestCase):
    def provider(self, up, popen, wait=5):
        folder = Path(tempfile.mkdtemp()) / "models"
        local = LocalProvider("http://127.0.0.1:11434/v1", models_dir=folder, start_wait=wait, popen=popen)
        self.addCleanup(local.stop)
        local.up = up
        return local, folder

    def test_starts_ollama_with_models_in_the_data_folder(self):
        calls, state = [], {"on": False}

        def popen(cmd, env, **kwargs):
            calls.append((cmd, env))
            state["on"] = True
            return SimpleNamespace(poll=lambda: None, terminate=lambda: None)

        local, folder = self.provider(lambda: state["on"], popen)
        with mock.patch.object(OpenAICompat, "chat", return_value=Reply({})):
            reply = local.chat({"model": "Lily_Local"})
        self.assertEqual(calls[0][0], ["ollama", "serve"])
        self.assertEqual(calls[0][1]["OLLAMA_MODELS"], str(folder))
        self.assertEqual(reply.routed_via, "Lily_Local")

    def test_does_not_start_it_when_it_is_already_running(self):
        local, _ = self.provider(lambda: True, lambda *a, **k: self.fail("started"))
        with mock.patch.object(OpenAICompat, "chat", return_value=Reply({}, "x")):
            self.assertEqual(local.chat({}).routed_via, "x")

    def test_start_failures_are_llm_errors(self):
        def missing(*args, **kwargs):
            raise FileNotFoundError("ollama")
        for popen, wait, text in ((missing, 5, "cannot start ollama"),
                                  (lambda *a, **k: SimpleNamespace(poll=lambda: 1), 5, "stopped right after"),
                                  (lambda *a, **k: SimpleNamespace(poll=lambda: None, terminate=lambda: None), 0, "did not answer")):
            local, _ = self.provider(lambda: False, popen, wait)
            with self.assertRaisesRegex(LLMError, text):
                local.chat({})


if __name__ == "__main__":
    unittest.main()
