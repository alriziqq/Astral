from tools import planner


def test_todo_due_date_creates_and_deletes_calendar_event(tmp_path, monkeypatch):
    monkeypatch.setattr(planner, "TODO_FILE", tmp_path / "todos.json")
    monkeypatch.setattr(planner, "CALENDAR_FILE", tmp_path / "calendar.json")
    todo = planner.create_todo("Kirim laporan", due_at="2026-09-04T09:00:00+07:00")
    assert planner.list_todos()[0]["id"] == todo["id"]
    assert planner.list_calendar_events()[0]["todo_id"] == todo["id"]
    assert planner.update_todo(todo["id"], status="done")["success"]
    assert planner.delete_todo(todo["id"])["success"]
    assert not planner.list_calendar_events()
