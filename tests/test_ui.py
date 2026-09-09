import ui as ui_module
from ui import TerminalUI
import threading

from agent import _thinking_status


class RecordingConsole:
    def __init__(self):
        self.calls = []

    def print(self, *args, **kwargs):
        self.calls.append((args, kwargs))


def test_thinking_renders_a_compact_elapsed_status():
    ui = TerminalUI()
    ui.console = RecordingConsole()

    ui.thinking("first status")
    ui.thinking("second status")

    assert len(ui.console.calls) == 2
    assert "•" in ui.console.calls[0][0][0]
    assert "Working" in ui.console.calls[0][0][0]
    assert "first status" not in ui.console.calls[0][0][0]
    assert "Working" in ui.console.calls[1][0][0]
    assert all(call[1].get("end") == "\r" for call in ui.console.calls)


def test_ui_can_share_the_cli_console():
    console = RecordingConsole()

    ui = TerminalUI(console=console)

    assert ui.console is console


def test_response_prefix_is_consistent():
    ui = TerminalUI()
    ui.console = RecordingConsole()

    ui.begin_response()

    assert ui.console.calls[-1][0][0] == "[bold cyan]Astral >[/] "
    assert ui.console.calls[-1][1]["end"] == ""


def test_reasoning_is_wrapped_in_parentheses():
    ui = TerminalUI()
    ui.console = RecordingConsole()

    ui.begin_reasoning()
    ui.end_reasoning()

    assert ui.console.calls[-3][0][0].endswith("([/]")
    assert ui.console.calls[-3][1]["end"] == ""
    assert ui.console.calls[-2][0][0] == "[dim])[/]"
    assert ui.console.calls[-1][0][0].startswith("[dim]")
    assert ui.console.calls[-1][0][0].endswith("[/]")


def test_divider_is_long_and_consistent():
    ui = TerminalUI()
    ui.console = RecordingConsole()

    ui.divider()

    assert ui.console.calls[-1][0][0].count("─") == 88


def test_internal_tool_activity_does_not_change_the_chat_transcript():
    ui = TerminalUI()
    ui.console = RecordingConsole()

    ui.tool("launch_application")
    ui.usage_details(10, 5, 15, 2, 1.0, 5.0, 0, 20)
    ui.tool_complete()

    assert ui.console.calls == []


def test_clear_thinking_erases_current_line():
    ui = TerminalUI()
    ui.console = RecordingConsole()

    ui.thinking("status")
    ui.clear_thinking()

    assert ui._thinking_visible is False
    assert ui.console.calls[-1][0][0] == " " * len("• Working (0s)")
    assert ui.console.calls[-1][1]["end"] == "\r"


def test_thinking_formats_elapsed_time_as_minutes(monkeypatch):
    ui = TerminalUI()
    ui.console = RecordingConsole()
    clock = iter([100.0, 100.0, 163.0])
    monkeypatch.setattr(ui_module.time, "monotonic", lambda: next(clock))

    ui.thinking("Working...")
    ui.thinking("Working...")

    assert "1m 3s" in ui.console.calls[-1][0][0]


def test_clear_thinking_can_preserve_elapsed_timer(monkeypatch):
    ui = TerminalUI()
    ui.console = RecordingConsole()
    clock = iter([100.0, 105.0, 108.0])
    monkeypatch.setattr(ui_module.time, "monotonic", lambda: next(clock))

    ui.thinking("Working...")
    ui.clear_thinking(reset=False)
    ui.thinking("Working...")

    assert "8s" in ui.console.calls[-1][0][0]


def test_thinking_renderer_failure_does_not_escape_worker():
    stop_event = threading.Event()

    def broken_renderer(_status):
        stop_event.set()
        raise RuntimeError("renderer unavailable")

    _thinking_status(stop_event, broken_renderer)
    assert stop_event.is_set()


def test_work_indicator_uses_a_single_consistent_status():
    stop_event = threading.Event()
    statuses = []

    def record(status):
        statuses.append(status)
        stop_event.set()

    _thinking_status(stop_event, record)

    assert statuses == ["Working..."]
