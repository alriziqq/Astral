from types import SimpleNamespace

from tools import applications


def test_launch_file_explorer_does_not_return_bootstrap_pid(monkeypatch):
    captured = {}

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(pid=1234)

    monkeypatch.setattr(
        applications.subprocess,
        "Popen",
        fake_popen,
    )

    result = applications.launch_application("File Explorer")

    assert result["success"] is True
    assert result["pid"] is None
    assert result["close_target"] == "explorer.exe"
    assert captured["kwargs"]["creationflags"] == applications._HIDDEN_CONSOLE


def test_start_menu_launch_uses_shell_execute(monkeypatch):
    launches = []

    def fake_popen(command, **kwargs):
        launches.append((command, kwargs))
        if command[0] == "Spotify":
            raise FileNotFoundError
        raise AssertionError("AppsFolder must use ShellExecute, not explorer.exe")

    monkeypatch.setattr(applications.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(
        applications,
        "list_launchable_applications",
        lambda *_args, **_kwargs: [{"name": "Spotify", "app_id": "SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify"}],
    )
    monkeypatch.setattr(
        applications.os,
        "startfile",
        lambda path: launches.append((path, {})),
    )

    result = applications.launch_application("Spotify")

    assert result["success"] is True
    assert result["method"] == "start_menu"
    assert launches[-1][0] == "shell:AppsFolder\\SpotifyAB.SpotifyMusic_zpdnekdrzrea0!Spotify"


def test_close_file_explorer_uses_shell_windows(monkeypatch):
    captured = {}

    def fake_run(command, **_kwargs):
        captured["command"] = command
        return SimpleNamespace(returncode=0, stdout="2\n", stderr="")

    monkeypatch.setattr(applications.subprocess, "run", fake_run)

    result = applications.close_application(process_name="explorer.exe")

    assert captured["command"][0] == "powershell.exe"
    assert "Shell.Application" in captured["command"][-1]
    assert result == {
        "success": True,
        "pid": None,
        "process_name": "explorer.exe",
        "closed_windows": 2,
        "message": "2 jendela File Explorer ditutup.",
    }


def test_close_application_verifies_the_process_stopped(monkeypatch):
    tasklist_outputs = iter([
        '"Example.exe","123","Console","1","10 K"\n',
        '',
        '',
    ])
    commands = []

    def fake_run(command, **_kwargs):
        commands.append(command)
        if command[0] == "tasklist":
            return SimpleNamespace(returncode=0, stdout=next(tasklist_outputs), stderr="")
        if command[0] == "powershell.exe":
            return SimpleNamespace(returncode=0, stdout="123\n", stderr="")
        raise AssertionError("taskkill must not be used after a graceful close succeeds")

    monkeypatch.setattr(applications.subprocess, "run", fake_run)
    monkeypatch.setattr(applications.time, "sleep", lambda _seconds: None)

    result = applications.close_application(pid=123)

    assert result["success"] is True
    assert result["graceful_close_requested"] == [123]
    assert result["force_killed_pids"] == []
    assert result["remaining_pids"] == []
    assert any(command[0] == "powershell.exe" for command in commands)


def test_close_application_hides_its_console_helpers(monkeypatch):
    tasklist_outputs = iter([
        '"Example.exe","123","Console","1","10 K"\n',
        '',
        '',
    ])
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        if command[0] == "tasklist":
            return SimpleNamespace(returncode=0, stdout=next(tasklist_outputs), stderr="")
        return SimpleNamespace(returncode=0, stdout="123\n", stderr="")

    monkeypatch.setattr(applications.subprocess, "run", fake_run)
    monkeypatch.setattr(applications.time, "sleep", lambda _seconds: None)

    applications.close_application(pid=123)

    helper_calls = [call for call in calls if call[0][0] != "tasklist"]
    assert helper_calls
    assert all(call[1]["creationflags"] == applications._HIDDEN_CONSOLE for call in helper_calls)


def test_list_applications_filters_by_executable_name(monkeypatch):
    monkeypatch.setattr(
        applications.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout=(
                '"notepad.exe","10","Console","1","10 K"\n'
                '"explorer.exe","20","Console","1","20 K"\n'
            ),
            stderr="",
        ),
    )

    assert applications.list_applications(query="explorer") == [
        {"name": "explorer.exe", "pid": 20, "memory": "20 K"},
    ]
