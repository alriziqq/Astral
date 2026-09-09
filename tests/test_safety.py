import json
from pathlib import Path

from agent import Agent
from tools import filesystem as fs


def test_filesystem_is_anchored_to_project_not_process_cwd():
    assert fs.WORKSPACE_ROOT == Path(__file__).parents[1].resolve()


def test_list_allowed_directory_reports_all_allowed_roots(monkeypatch, tmp_path):
    workspace = tmp_path / "workspace"
    user_root = tmp_path / "user"
    d_root = tmp_path / "d-drive"
    monkeypatch.setattr(fs, "WORKSPACE_ROOT", workspace)
    monkeypatch.setattr(fs, "ASTRAL_USER_ROOT", user_root)
    monkeypatch.setattr(fs, "ASTRAL_D_ROOT", d_root)

    result = fs.list_allowed_directory()

    assert result["success"] is True
    assert [item["path"] for item in result["directories"]] == [
        str(workspace), str(user_root), str(d_root)
    ]
    assert all(item["write_requires_confirmation"] for item in result["directories"])


def test_absolute_path_inside_user_root_is_allowed(tmp_path, monkeypatch):
    user_root = tmp_path / "user"
    user_root.mkdir()
    monkeypatch.setattr(fs, "WORKSPACE_ROOT", tmp_path / "workspace")
    monkeypatch.setattr(fs, "ASTRAL_USER_ROOT", user_root)

    target = user_root / "notes.txt"
    result = fs.write_file(str(target), "hello")

    assert result["success"] is True
    assert target.read_text(encoding="utf-8") == "hello"


def test_absolute_path_outside_allowed_roots_is_denied(tmp_path, monkeypatch):
    monkeypatch.setattr(fs, "WORKSPACE_ROOT", tmp_path / "workspace")
    monkeypatch.setattr(fs, "ASTRAL_USER_ROOT", tmp_path / "user")
    monkeypatch.setattr(fs, "ASTRAL_D_ROOT", tmp_path / "d-drive")

    try:
        fs.read_file(str(tmp_path / "outside.txt"))
    except PermissionError as error:
        assert "di luar root filesystem" in str(error)
    else:
        raise AssertionError("Path di luar root seharusnya ditolak")


def test_absolute_path_inside_d_root_is_allowed(tmp_path, monkeypatch):
    d_root = tmp_path / "d-drive"
    d_root.mkdir()
    monkeypatch.setattr(fs, "WORKSPACE_ROOT", tmp_path / "workspace")
    monkeypatch.setattr(fs, "ASTRAL_USER_ROOT", tmp_path / "user")
    monkeypatch.setattr(fs, "ASTRAL_D_ROOT", d_root)

    target = d_root / "shared.txt"
    result = fs.write_file(str(target), "hello")

    assert result["success"] is True
    assert target.read_text(encoding="utf-8") == "hello"


def test_mutating_tool_is_denied_without_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(fs, "WORKSPACE_ROOT", tmp_path)
    agent = Agent(confirm_action=None)

    result = agent._execute_tool({
        "name": "write_file",
        "arguments": json.dumps({"path": "blocked.txt", "content": "no"}),
    })

    assert "dibatalkan" in result
    assert not (tmp_path / "blocked.txt").exists()


def test_mutating_tool_runs_after_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(fs, "WORKSPACE_ROOT", tmp_path)
    agent = Agent(confirm_action=lambda _name, _arguments: True)

    result = agent._execute_tool({
        "name": "write_file",
        "arguments": json.dumps({"path": "allowed.txt", "content": "yes"}),
    })

    assert '"success": true' in result
    assert (tmp_path / "allowed.txt").read_text(encoding="utf-8") == "yes"


def test_large_tool_results_are_limited(monkeypatch):
    monkeypatch.setattr("agent.MAX_TOOL_RESULT_CHARS", 10)
    result = Agent._limit_tool_result("x" * 11)
    assert result.startswith("x" * 10)
    assert "dipotong" in result


def test_shell_tool_is_denied_without_confirmation():
    agent = Agent(confirm_action=None)
    result = agent._execute_tool({
        "name": "run_shell_command",
        "arguments": json.dumps({"command": "Write-Output unsafe"}),
    })
    assert "dibatalkan" in result


def test_shell_tool_executes_after_confirmation():
    agent = Agent(confirm_action=lambda _name, _arguments: True)
    result = agent._execute_tool({
        "name": "run_shell_command",
        "arguments": json.dumps({"command": "Write-Output streamed"}),
    })
    assert '"success": true' in result
    assert "streamed" in result
