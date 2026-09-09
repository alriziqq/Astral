"""Local todo, calendar, and desktop-clock tools."""
import json
import threading
from datetime import datetime
from uuid import uuid4
from config import WORKSPACE_ROOT

TODO_FILE = WORKSPACE_ROOT / "data" / "todos.json"
CALENDAR_FILE = WORKSPACE_ROOT / "data" / "calendar.json"
_LOCK = threading.Lock()

def _load(path):
    if not path.exists(): return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list): raise RuntimeError(f"{path.name} harus JSON array.")
    return data

def _save(path, items):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    temp.replace(path)

def desktop_time():
    now = datetime.now().astimezone()
    return {"local_time": now.isoformat(), "timezone": str(now.tzinfo), "unix_timestamp": int(now.timestamp())}

def create_todo(title, description="", due_at=None):
    if not isinstance(title, str) or not title.strip(): raise ValueError("title wajib string non-kosong.")
    if due_at is not None:
        try: datetime.fromisoformat(due_at.replace("Z", "+00:00"))
        except ValueError as error: raise ValueError("due_at harus ISO-8601.") from error
    item = {"id": uuid4().hex, "title": title.strip(), "description": description if isinstance(description, str) else "", "status": "open", "due_at": due_at, "calendar_event_id": None, "created_at": datetime.now().astimezone().isoformat()}
    with _LOCK:
        todos = _load(TODO_FILE); events = _load(CALENDAR_FILE)
        if due_at:
            event = {"id": uuid4().hex, "title": item["title"], "start_at": due_at, "end_at": None, "todo_id": item["id"]}
            events.append(event); item["calendar_event_id"] = event["id"]
        todos.append(item); _save(TODO_FILE, todos); _save(CALENDAR_FILE, events)
    return item

def list_todos(status=None):
    with _LOCK: items = _load(TODO_FILE)
    return [x for x in items if status is None or x.get("status") == status]

def update_todo(todo_id, title=None, description=None, status=None, due_at=None):
    if status is not None and status not in {"open", "done", "cancelled"}: raise ValueError("status: open, done, atau cancelled.")
    with _LOCK:
        todos = _load(TODO_FILE); item = next((x for x in todos if x.get("id") == todo_id), None)
        if not item: return {"success": False, "error": "Todo tidak ditemukan."}
        for key, value in {"title": title, "description": description, "status": status, "due_at": due_at}.items():
            if value is not None: item[key] = value
        _save(TODO_FILE, todos)
    return {"success": True, "todo": item}

def delete_todo(todo_id):
    with _LOCK:
        todos = _load(TODO_FILE); selected = next((x for x in todos if x.get("id") == todo_id), None)
        if not selected: return {"success": False, "error": "Todo tidak ditemukan."}
        _save(TODO_FILE, [x for x in todos if x.get("id") != todo_id])
        if selected.get("calendar_event_id"):
            _save(CALENDAR_FILE, [x for x in _load(CALENDAR_FILE) if x.get("id") != selected["calendar_event_id"]])
    return {"success": True, "id": todo_id}

def list_calendar_events():
    with _LOCK: return sorted(_load(CALENDAR_FILE), key=lambda x: x.get("start_at", ""))
