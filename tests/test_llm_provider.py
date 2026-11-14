"""Tests the real HTTP provider against a tiny fake router on localhost."""
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from lily.llm.providers.openai_compat import OpenAICompat
from lily.utils.errors import LLMError

ANSWER = {"choices": [{"message": {"content": "hi"}}]}


class FakeRouter(BaseHTTPRequestHandler):
    def do_POST(self):
        size = int(self.headers.get("Content-Length", 0))
        self.server.seen = {
            "path": self.path,
            "auth": self.headers.get("Authorization"),
            "body": json.loads(self.rfile.read(size)),
        }
        mode = self.server.mode
        status = 500 if mode == "http500" else 200
        body = b"not json" if mode == "badjson" else json.dumps(ANSWER).encode()
        if mode == "http500":
            body = b"upstream exploded"
        self.send_response(status)
        self.send_header("X-Routed-Via", "groq/llama-3")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class ProviderTests(unittest.TestCase):
    def setUp(self):
        env = mock.patch.dict(os.environ, {"no_proxy": "127.0.0.1", "NO_PROXY": "127.0.0.1"})
        env.start()
        self.addCleanup(env.stop)
        self.server = HTTPServer(("127.0.0.1", 0), FakeRouter)
        self.server.mode, self.server.seen = "ok", {}
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = f"http://127.0.0.1:{self.server.server_port}/v1"

    def test_success_returns_data_and_routed_via(self):
        provider = OpenAICompat(self.base + "/", api_key="secret", timeout=5)
        reply = provider.chat({"model": "auto", "messages": []})
        self.assertEqual(reply.data, ANSWER)
        self.assertEqual(reply.routed_via, "groq/llama-3")

    def test_sends_path_auth_and_body(self):
        OpenAICompat(self.base, api_key="secret", timeout=5).chat({"model": "auto:fast"})
        seen = self.server.seen
        self.assertEqual(seen["path"], "/v1/chat/completions")
        self.assertEqual(seen["auth"], "Bearer secret")
        self.assertEqual(seen["body"], {"model": "auto:fast"})

    def test_no_key_means_no_auth_header(self):
        OpenAICompat(self.base, timeout=5).chat({"model": "auto"})
        self.assertIsNone(self.server.seen["auth"])

    def test_http_error_becomes_llm_error(self):
        self.server.mode = "http500"
        with self.assertRaises(LLMError) as ctx:
            OpenAICompat(self.base, timeout=5).chat({"model": "auto"})
        self.assertIn("500", str(ctx.exception))
        self.assertIn("upstream exploded", str(ctx.exception))

    def test_invalid_json_becomes_llm_error(self):
        self.server.mode = "badjson"
        with self.assertRaises(LLMError):
            OpenAICompat(self.base, timeout=5).chat({"model": "auto"})

    def test_unreachable_router_becomes_llm_error(self):
        self.server.shutdown()
        self.server.server_close()
        with self.assertRaises(LLMError) as ctx:
            OpenAICompat(self.base, timeout=2).chat({"model": "auto"})
        self.assertIn("cannot reach", str(ctx.exception))
        self.addCleanup(lambda: None)


if __name__ == "__main__":
    unittest.main()
