"""Search tool tests use a local fake page, never the real DuckDuckGo."""
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest import mock

from lily.tools.builtin.web_search import Tool
from lily.tools.helpers.ddg import parse
from lily.utils.errors import ToolError

PAGE = """<html><body>
<div class="result"><h2 class="result__title">
<a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Ftermux.dev%2F&amp;rut=abc">
Termux <b>Wiki</b></a></h2>
<a class="result__snippet" href="x">A terminal &amp; Linux <b>environment</b> for Android.</a></div>
<div class="result"><h2><a class="result__a" href="https://example.org/plain">Plain link</a></h2></div>
<div class="result"><a class="result__a" href="https://third.example">Third</a>
<a class="result__snippet">Third snippet</a></div>
</body></html>"""


class FakeSearch(BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.queries.append(self.path)
        body = (b"<html>nothing</html>" if self.server.empty else PAGE.encode())
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class ParserTests(unittest.TestCase):
    def test_titles_links_and_snippets_are_extracted(self):
        results = parse(PAGE)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["title"], "Termux Wiki")
        self.assertEqual(results[0]["url"], "https://termux.dev/")
        self.assertEqual(results[0]["snippet"], "A terminal & Linux environment for Android.")

    def test_plain_links_and_missing_snippets(self):
        results = parse(PAGE)
        self.assertEqual(results[1]["url"], "https://example.org/plain")
        self.assertEqual(results[1]["snippet"], "")
        self.assertEqual(results[2]["snippet"], "Third snippet")


class WebSearchToolTests(unittest.TestCase):
    def serve(self, empty=False):
        server = HTTPServer(("127.0.0.1", 0), FakeSearch)
        server.queries, server.empty = [], empty
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        env = {"LILY_SEARCH_URL": f"http://127.0.0.1:{server.server_port}/html/",
               "no_proxy": "127.0.0.1", "NO_PROXY": "127.0.0.1"}
        patch = mock.patch.dict(os.environ, env)
        patch.start()
        self.addCleanup(patch.stop)
        return server

    def test_numbered_results_with_links(self):
        server = self.serve()
        out = Tool(None).execute({"query": "termux wiki", "limit": 2})
        self.assertTrue(out.startswith("1. Termux Wiki\n   https://termux.dev/\n   A terminal"))
        self.assertIn("2. Plain link", out)
        self.assertNotIn("3.", out)
        self.assertIn("q=termux+wiki", server.queries[0])

    def test_no_results_is_a_clear_error(self):
        self.serve(empty=True)
        with self.assertRaisesRegex(ToolError, "no results"):
            Tool(None).execute({"query": "anything"})

    def test_unreachable_search_page(self):
        server = self.serve()
        server.shutdown()
        server.server_close()
        with self.assertRaisesRegex(ToolError, "search failed"):
            Tool(None).execute({"query": "anything"})


if __name__ == "__main__":
    unittest.main()
