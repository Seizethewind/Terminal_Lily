"""All terminal output goes through here (rich)."""
from contextlib import contextmanager

from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel


class Renderer:
    def __init__(self):
        self.console = Console()
        self._status = None   # the spinner, while Lily is thinking

    def banner(self, model):
        body = "[bold magenta]Lily[/] - terminal agent\nType /help for commands."
        self.console.print(Panel(body, subtitle=f"model: {escape(model)}"))

    def reply(self, text):
        self.console.print(Markdown(text))

    def info(self, text):
        self.console.print(escape(text), style="dim")

    def error(self, text):
        self.console.print(f"[bold red]Error:[/] {escape(text)}")

    @contextmanager
    def thinking(self):
        """Use as: with ui.thinking(): ... (shows a spinner)."""
        self._status = self.console.status("[dim]thinking...[/]")
        self._status.start()
        try:
            yield
        finally:
            self._status.stop()
            self._status = None

    def ask(self, prompt="you"):
        return self.console.input(f"[bold cyan]{prompt}>[/] ")

    def confirm(self, question):
        status = self._status
        if status:
            status.stop()   # the spinner would draw over the question
        try:
            head, _, body = question.partition("\n")
            self.console.print(f"\n[bold]{escape(head)}[/]")
            if body:
                self.console.print(escape(body), style="dim", highlight=False)
            answer = self.console.input(f"[bold cyan]{escape('Allow? [y/N]')}[/] ")
        finally:
            if status:
                status.start()
        return answer.strip().lower() in ("y", "yes")
