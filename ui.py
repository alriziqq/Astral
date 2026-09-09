"""Rich terminal renderer for Astral's interactive agent experience."""
import time

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class TerminalUI:
    # Terminal stability contract: internal model/tool activity must never add
    # lines to the chat transcript. Keep this false unless the user explicitly
    # asks for diagnostic output.
    SHOW_INTERNAL_STATUS = False

    def __init__(self, console: Console | None = None):
        # CMD.exe does not reliably support Live's cursor-control redraw.
        # Keep rendering append-only so it is also stable in legacy consoles.
        self.console = console or Console(legacy_windows=True)
        self._thinking_visible = False
        self._thinking_started_at: float | None = None
        self._thinking_width = 0

    def header(self, model: str):
        self.console.clear()
        self.console.print(Panel(
            "[bold cyan]ASTRAL[/]  [dim]local agent harness[/]",
            subtitle=f"[dim]{model}  |  streaming[/]",
            box=box.ASCII, border_style="blue", padding=(0, 2),
        ))
        self.console.print("[dim]Ask anything  |  /help for commands  |  Ctrl+C to exit[/]\n")

    def divider(self, width: int = 88):
        """Separate a user prompt from Astral's streamed answer."""
        self.console.print("[dim]" + ("─" * width) + "[/]")

    def thinking(self, status: str):
        """Render the compact, continuously updating work indicator."""
        # A single carriage-returned line follows the compact Codex/Claude
        # style while remaining reliable in legacy Windows terminals where
        # Rich Live can corrupt streamed text.
        if self._thinking_started_at is None:
            self._thinking_started_at = time.monotonic()

        elapsed = int(time.monotonic() - self._thinking_started_at)
        minutes, seconds = divmod(elapsed, 60)
        elapsed_text = f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
        line = f"• Working ({elapsed_text})"
        self._thinking_width = max(self._thinking_width, len(line))
        self.console.print(
            "[cyan]•[/] [bold]Working[/] [dim](" + elapsed_text + ")[/]",
            end="\r",
        )
        self._thinking_visible = True

    def clear_thinking(self, reset: bool = True):
        """Erase the indicator, optionally retaining its elapsed timer."""
        if self._thinking_visible:
            # Clear the previous (possibly longer) status before the next
            # renderer writes at column zero.
            self.console.print(" " * self._thinking_width, end="\r", markup=False)
        self._thinking_visible = False
        if reset:
            self._thinking_started_at = None
        self._thinking_width = 0

    def begin_response(self):
        self.clear_thinking()
        self.console.print("[bold cyan]Astral >[/] ", end="")

    def begin_reasoning(self):
        """Start the optional, streamed model-reasoning transcript."""
        self.clear_thinking()
        self.console.print("[dim cyan]Reasoning >[/] [dim]([/]", end="")

    def stream_reasoning(self, text: str):
        self.console.print(
            Text(text, style="dim"), end="", markup=False, highlight=False
        )

    def end_reasoning(self):
        self.console.print("[dim])[/]")
        self.divider()

    def stream(self, text: str):
        self.console.print(Text(text), end="", markup=False, highlight=False)

    def end_response(self):
        self.console.print()

    def tool(self, name: str):
        if not self.SHOW_INTERNAL_STATUS:
            return
        self.clear_thinking(reset=False)
        self.console.print(f"[dim]+--[/] [bold yellow]tool[/] {name}")

    def tool_complete(self):
        if not self.SHOW_INTERNAL_STATUS:
            return
        self.console.print("[dim]   completed | continuing...[/]")

    def usage(self, prompt: int, completion: int, elapsed: float):
        if not self.SHOW_INTERNAL_STATUS:
            return
        self.console.print(f"[dim]   {prompt:,} in · {completion:,} out · {elapsed:.1f}s[/]")

    def error(
        self,
        message: str,
        detail: str | None = None,
        hint: str | None = None,
    ):
        """Show a recoverable error without ending the interactive session."""
        self.clear_thinking()
        body = Text(message, style="bold red")
        if detail:
            body.append("\n" + detail, style="dim")
        if hint:
            body.append("\n" + hint, style="yellow")
        self.console.print(Panel(body, title="Error", border_style="red"))

    def usage_details(
        self,
        prompt: int,
        completion: int,
        total: int,
        reasoning: int,
        elapsed: float,
        tps: float,
        visible_content: int,
        tool_payload: int,
    ):
        """Render complete request statistics through the Rich console."""
        if not self.SHOW_INTERNAL_STATUS:
            return
        self.console.print(
            f"[dim]   {prompt:,} in · {completion:,} out · "
            f"{total:,} total · {reasoning:,} reasoning · "
            f"{tps:.1f} tok/s · {elapsed:.1f}s · visible {visible_content} · "
            f"tool {tool_payload}[/]"
        )
