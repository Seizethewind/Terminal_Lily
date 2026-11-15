"""Termux commands are replaced by tiny fake scripts placed first on PATH."""
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lily.tools.builtin.termux_api import Tool
from lily.utils.errors import ToolError

SCRIPTS = {
    "termux-battery-status": 'echo \'{"percentage": 87}\'',
    "termux-clipboard-get": "echo copied text",
    "termux-clipboard-set": 'cat > "$FAKE_DIR/clip"',
    "termux-notification": 'echo "$@" > "$FAKE_DIR/notify"',
    "termux-toast": 'echo "$@" > "$FAKE_DIR/toast"',
}


class TermuxApiTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        for name, body in SCRIPTS.items():
            script = self.dir / name
            script.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
            script.chmod(script.stat().st_mode | stat.S_IEXEC)
        env = {"PATH": f"{self.dir}:{os.environ['PATH']}", "FAKE_DIR": str(self.dir)}
        patch = mock.patch.dict(os.environ, env)
        patch.start()
        self.addCleanup(patch.stop)
        self.tool = Tool(None)

    def test_battery(self):
        self.assertEqual(self.tool.execute({"action": "battery"}), '{"percentage": 87}')

    def test_clipboard_round_trip(self):
        self.assertEqual(self.tool.execute({"action": "clipboard_get"}), "copied text")
        self.assertEqual(self.tool.execute({"action": "clipboard_set", "text": "hello"}), "done")
        self.assertEqual((self.dir / "clip").read_text(encoding="utf-8"), "hello")

    def test_notification_uses_title_and_text(self):
        self.tool.execute({"action": "notify", "title": "Hi", "text": "body"})
        self.assertEqual((self.dir / "notify").read_text(encoding="utf-8").strip(),
                         "--title Hi --content body")

    def test_toast(self):
        self.tool.execute({"action": "toast", "text": "yo"})
        self.assertEqual((self.dir / "toast").read_text(encoding="utf-8").strip(), "yo")

    def test_missing_text_and_unknown_action(self):
        with self.assertRaisesRegex(ToolError, "needs the 'text'"):
            self.tool.execute({"action": "toast"})
        with self.assertRaisesRegex(ToolError, "unknown action"):
            self.tool.execute({"action": "launch_missiles"})

    def test_not_installed_gives_a_hint(self):
        with mock.patch.dict(os.environ, {"PATH": "/nonexistent"}):
            with self.assertRaisesRegex(ToolError, "pkg install termux-api"):
                self.tool.execute({"action": "battery"})

    def test_failing_command_is_reported(self):
        (self.dir / "termux-battery-status").write_text("#!/bin/sh\necho bad >&2\nexit 2\n")
        with self.assertRaisesRegex(ToolError, "failed: bad"):
            self.tool.execute({"action": "battery"})


if __name__ == "__main__":
    unittest.main()
