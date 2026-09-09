import json
from types import SimpleNamespace

from agent import Agent
from tools import shell


class RecordingUI:
    def __init__(self):
        self.calls = []

    def thinking(self, status):
        self.calls.append(("thinking", status))

    def clear_thinking(self, reset=True):
        self.calls.append(("clear_thinking",))

    def begin_response(self):
        self.calls.append(("begin_response",))

    def begin_reasoning(self):
        self.calls.append(("begin_reasoning",))

    def stream_reasoning(self, content):
        self.calls.append(("stream_reasoning", content))

    def end_reasoning(self):
        self.calls.append(("end_reasoning",))

    def stream(self, content):
        self.calls.append(("stream", content))

    def end_response(self):
        self.calls.append(("end_response",))

    def tool(self, name):
        self.calls.append(("tool", name))

    def tool_complete(self):
        self.calls.append(("tool_complete",))

    def usage_details(self, *args):
        self.calls.append(("usage_details", *args))

    def error(self, message, detail=None, hint=None):
        self.calls.append(("error", message, detail, hint))


def _tool_delta(name, arguments, call_id):
    return SimpleNamespace(
        content=None,
        reasoning_content=None,
        tool_calls=[SimpleNamespace(
            index=0,
            id=call_id,
            function=SimpleNamespace(
                name=name,
                arguments=json.dumps(arguments),
            ),
        )],
    )


def _usage():
    return {
        "type": "usage",
        "data": SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
            completion_tokens_details=SimpleNamespace(reasoning_tokens=2),
        ),
        "elapsed": 0.2,
    }


def test_chained_tools_share_one_renderer_without_stdout(capsys):
    ui = RecordingUI()
    agent = Agent(confirm_action=lambda _name, _args: True, ui=ui)
    calls = iter([
        ("run_shell_command", {"command": "Write-Output captured"}, "shell-1"),
        ("list_directory", {"path": "."}, "list-1"),
    ])

    def chat_stream(_messages, temperature, tools):
        try:
            name, arguments, call_id = next(calls)
        except StopIteration:
            yield {"type": "delta", "data": SimpleNamespace(
                content="done", reasoning_content=None, tool_calls=None,
            )}
            yield _usage()
            return
        yield {"type": "delta", "data": _tool_delta(name, arguments, call_id)}
        yield _usage()

    agent.llm.chat_stream = chat_stream
    agent.TOOL_HANDLERS = {
        **agent.TOOL_HANDLERS,
        "run_shell_command": lambda **_args: {"success": True, "stdout": "captured", "stderr": ""},
        "list_directory": lambda **_args: {"success": True, "items": []},
    }

    messages = [{"role": "user", "content": "inspect files"}]
    assert agent.process_message(messages) == "done"

    assert [call[1] for call in ui.calls if call[0] == "tool"] == [
        "run_shell_command", "list_directory",
    ]
    assert len([call for call in ui.calls if call[0] == "usage_details"]) == 3
    assert capsys.readouterr().out == ""


def test_shell_output_is_returned_not_printed(monkeypatch, capsys):
    def fake_run(*args, **kwargs):
        assert kwargs["capture_output"] is True
        assert kwargs["creationflags"] == getattr(shell.subprocess, "CREATE_NO_WINDOW", 0)
        return SimpleNamespace(returncode=0, stdout="out\n", stderr="err\n")

    monkeypatch.setattr(shell.subprocess, "run", fake_run)
    result = shell.run_shell_command("Write-Output out")

    assert result["stdout"] == "out\n"
    assert result["stderr"] == "err\n"
    assert capsys.readouterr().out == ""


def test_failed_request_clears_thinking_before_reporting_error():
    ui = RecordingUI()
    agent = Agent(ui=ui)

    def chat_stream(_messages, temperature, tools):
        raise RuntimeError("network unavailable")
        yield  # pragma: no cover - keeps this function a generator

    agent.llm.chat_stream = chat_stream

    assert agent.process_message([{"role": "user", "content": "hello"}]) == (
        "Astral mengalami error saat menghubungi model."
    )
    assert ("clear_thinking",) in ui.calls


def test_reasoning_can_be_streamed_before_the_response():
    ui = RecordingUI()
    agent = Agent(ui=ui)
    agent.reasoning_enabled = True

    def chat_stream(_messages, temperature, tools):
        yield {"type": "delta", "data": SimpleNamespace(
            content=None, reasoning_content="checking facts...", tool_calls=None,
        )}
        yield {"type": "delta", "data": SimpleNamespace(
            content="done", reasoning_content=None, tool_calls=None,
        )}
        yield _usage()

    agent.llm.chat_stream = chat_stream

    assert agent.process_message([{"role": "user", "content": "hello"}]) == "done"
    assert ui.calls.index(("begin_reasoning",)) < ui.calls.index(("stream_reasoning", "checking facts..."))
    assert ui.calls.index(("stream_reasoning", "checking facts...")) < ui.calls.index(("end_reasoning",))
    assert ui.calls.index(("end_reasoning",)) < ui.calls.index(("begin_response",))
