"""All terminal output goes through here (rich)."""
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.panel import Panel


class Renderer:
    def __init__(self):
        self.console = Console()

    def banner(self, model):
        body = "[bold magenta]Lily[/] - terminal agent\nType /help for commands."
        self.console.print(Panel(body, subtitle=f"model: {escape(model)}"))

    def reply(self, text):
        self.console.print(Markdown(text))

    def info(self, text):
        self.console.print(escape(text), style="dim")

    def error(self, text):
        self.console.print(f"[bold red]Error:[/] {escape(text)}")

    def thinking(self):
        """Use as: with ui.thinking(): ... (shows a spinner)."""
        return self.console.status("[dim]thinking...[/]")

    def ask(self, prompt="you"):
        return self.console.input(f"[bold cyan]{prompt}>[/] ")

    def confirm(self, question):
        answer = self.console.input(f"[yellow]{escape(question)} [y/N][/] ")
        return answer.strip().lower() in ("y", "yes")
