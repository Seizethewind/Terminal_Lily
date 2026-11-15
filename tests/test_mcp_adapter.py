import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lily.orchestrator import Lily
from lily.tools.mcp import adapter
from lily.tools.mcp.config import load_servers
from lily.utils.errors import ConfigError, ToolError
from tests.fake_mcp import start_server
from tests.fakes import make_settings


def entry(url, name="lilyai", auth_env="", token=""):
    return {"name": name, "url": url, "auth_env": auth_env, "token": token}


class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.lily = Lily(make_settings())

    def test_remote_tools_become_lily_tools(self):
        server = start_server(self, token="tok")
        tools, errors = adapter.load(self.lily, [entry(server.url, auth_env="T", token="tok")])
        self.assertEqual(errors, [])
        self.assertEqual([t.name for t in tools], ["lilyai__echo", "lilyai__boom"])
        self.assertEqual(tools[0].schema()["function"]["parameters"]["required"], ["text"])
        self.assertEqual(tools[1].parameters, {"type": "object", "properties": {}})

    def test_running_a_wrapped_tool_calls_the_server(self):
        server = start_server(self)
        tools, _ = adapter.load(self.lily, [entry(server.url)])
        self.assertEqual(tools[0].execute({"text": "hey"}), "HEY")
        with self.assertRaises(ToolError):
            tools[0].execute({})   # missing required argument, caught before the call

    def test_missing_token_is_reported_without_connecting(self):
        server = start_server(self)
        tools, errors = adapter.load(self.lily, [entry(server.url, auth_env="LILYAI_MCP_TOKEN")])
        self.assertEqual(tools, [])
        self.assertIn("LILYAI_MCP_TOKEN is not set", errors[0])
        self.assertEqual(server.log, [])

    def test_unreachable_server_is_reported_and_others_still_load(self):
        good = start_server(self)
        dead = start_server(self)
        dead.shutdown()
        dead.server_close()
        servers = [entry(dead.url, name="dead"), entry(good.url, name="good")]
        tools, errors = adapter.load(self.lily, servers)
        self.assertEqual(len(tools), 2)
        self.assertIn("mcp dead", errors[0])


class ConfigTests(unittest.TestCase):
    def write(self, text):
        path = Path(tempfile.mkdtemp()) / "mcp_servers.toml"
        path.write_text(text, encoding="utf-8")
        return path

    def test_disabled_servers_are_skipped(self):
        path = self.write('[[servers]]\nname = "a"\nurl = "http://x"\nenabled = false\n')
        self.assertEqual(load_servers(path), [])

    def test_token_comes_from_the_environment(self):
        path = self.write('[[servers]]\nname = "a"\nurl = "http://x"\nauth_env = "MY_TOK"\n')
        with mock.patch.dict(os.environ, {"MY_TOK": "abc"}):
            self.assertEqual(load_servers(path)[0]["token"], "abc")

    def test_missing_file_means_no_servers(self):
        self.assertEqual(load_servers(Path("/nonexistent/mcp_servers.toml")), [])

    def test_server_without_url_is_a_config_error(self):
        with self.assertRaises(ConfigError):
            load_servers(self.write('[[servers]]\nname = "a"\n'))

    def test_the_shipped_config_has_the_lilyai_server_switched_off(self):
        self.assertEqual(load_servers(), [])


if __name__ == "__main__":
    unittest.main()
