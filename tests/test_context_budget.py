import json

from agent import Agent


def test_compact_tool_schema_removes_non_validation_metadata():
    raw = len(json.dumps(Agent.TOOLS, ensure_ascii=False))
    compact = Agent._compact_tool_definitions(Agent.TOOLS)

    assert len(json.dumps(compact, ensure_ascii=False)) < raw
    properties = compact[0]["function"]["parameters"]["properties"]
    assert all("description" not in value for value in properties.values())


def test_history_keeps_tool_call_pair_but_limits_payload(monkeypatch):
    monkeypatch.setattr("agent.MAX_CONTEXT_TURNS", 1)
    monkeypatch.setattr("agent.MAX_HISTORY_TOOL_RESULT_CHARS", 20)
    messages = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old answer"},
        {"role": "user", "content": "new"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [{"id": "call-1", "type": "function"}],
        },
        {"role": "tool", "tool_call_id": "call-1", "content": "x" * 100},
    ]

    compacted = Agent._compact_history(messages)

    assert compacted[0]["role"] == "user"
    assert compacted[-1]["tool_call_id"] == "call-1"
    assert len(compacted[-1]["content"]) > 20  # marker explains truncation
    assert "dipotong" in compacted[-1]["content"]
