"""The input/output loop."""
from lily.ui import commands
from lily.ui.renderer import Renderer
from lily.utils.errors import LilyError
from lily.utils.logger import get_logger

log = get_logger("ui")


class Terminal:
    def __init__(self, lily, ui=None):
        self.lily = lily
        self.ui = ui or Renderer()
        self.lily.confirm = self.ui.confirm

    def run(self):
        self.ui.banner(self.lily.model)
        while True:
            try:
                line = self.ui.ask().strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line:
                continue
            if line.startswith("/"):
                if self._command(line):
                    break
            else:
                self._chat(line)
        self.ui.info("Bye!")

    def _command(self, line):
        """Run a slash command. Returns True when Lily should exit."""
        try:
            out = commands.run(self.lily, line)
        except LilyError as err:
            self.ui.error(str(err))
            return False
        if out == commands.EXIT:
            return True
        self.ui.info(out)
        return False

    def _chat(self, text):
        try:
            with self.ui.thinking():
                reply = self.lily.handle(text)
            self.ui.reply(reply)
        except KeyboardInterrupt:
            self.ui.info("(cancelled)")
        except LilyError as err:
            self.ui.error(str(err))
        except Exception:
            log.exception("unexpected error")
            self.ui.error("something went wrong, see data/lily.log")
