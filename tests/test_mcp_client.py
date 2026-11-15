import unittest

from lily.tools.mcp.client import McpClient
from lily.utils.errors import ToolError
from tests.fake_mcp import start_server


class McpClientTests(unittest.TestCase):
    def connected(self, **options):
        server = start_server(self, **options)
        client = McpClient(server.url, token=options.get("token", ""), timeout=5)
        client.connect()
        return server, client

    def test_handshake_sends_initialize_then_initialized(self):
        server, _ = self.connected()
        self.assertEqual([r["method"] for r in server.log], ["initialize", "notifications/initialized"])

    def test_session_id_is_sent_back(self):
        server, client = self.connected()
        client.list_tools()
        self.assertIsNone(server.log[0]["session"])
        self.assertEqual({r["session"] for r in server.log[1:]}, {"sess1"})

    def test_list_tools_follows_pagination(self):
        _, client = self.connected()
        self.assertEqual([t["name"] for t in client.list_tools()], ["echo", "boom"])

    def test_call_tool_returns_text(self):
        _, client = self.connected()
        self.assertEqual(client.call_tool("echo", {"text": "hi"}), "HI")

    def test_tool_error_result_becomes_tool_error(self):
        _, client = self.connected()
        with self.assertRaises(ToolError) as ctx:
            client.call_tool("boom", {})
        self.assertIn("kaput", str(ctx.exception))

    def test_event_stream_replies_work_too(self):
        _, client = self.connected(sse=True)
        self.assertEqual(client.call_tool("echo", {"text": "sse"}), "SSE")
        self.assertEqual(len(client.list_tools()), 2)

    def test_bearer_token_is_sent(self):
        server, client = self.connected(token="s3cret")
        client.list_tools()
        self.assertEqual({r["auth"] for r in server.log}, {"Bearer s3cret"})

    def test_wrong_token_is_reported(self):
        server = start_server(self, token="right")
        with self.assertRaises(ToolError) as ctx:
            McpClient(server.url, token="wrong", timeout=5).connect()
        self.assertIn("401", str(ctx.exception))

    def test_json_rpc_error_becomes_tool_error(self):
        _, client = self.connected()
        with self.assertRaises(ToolError) as ctx:
            client._rpc("nope/nothing", {})
        self.assertIn("method not found", str(ctx.exception))

    def test_unreachable_server(self):
        server = start_server(self)
        server.shutdown()
        server.server_close()
        with self.assertRaises(ToolError) as ctx:
            McpClient(server.url, timeout=2).connect()
        self.assertIn("cannot reach", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
