"""JSONL bridge between the Tauri window and Astral's Python agent.

The bridge keeps the existing Agent implementation intact. Tauri writes one
JSON command per line to stdin; this process emits streaming UI events on
stdout. It is intentionally small so it can later be bundled as a sidecar.
"""

from __future__ import annotations

import json
import queue
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent import Agent
from config import LLM_PROVIDER, PROJECT_ROOT, get_llm_config
from tools.memory import delete_memory, list_memories, save_memory, update_memory

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


SYSTEM_PROMPT = """You are Astral, a local AI assistant. Call the user 'bos'.
Be helpful, accurate, practical, and concise. Use tools when useful. Never
claim an action was performed unless the tool returned a successful result.
Ask for confirmation before modifying files, running shell commands, changing
memory, launching applications, or changing todos.
"""


commands: queue.Queue[dict[str, Any]] = queue.Queue()
output_lock = threading.Lock()
pending_permissions: dict[str, dict[str, Any]] = {}
pending_lock = threading.Lock()
always_allowed_tools: set[str] = set()
cancel_request = threading.Event()
messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
request_active = False
current_provider = LLM_PROVIDER
DATA_DIR = PROJECT_ROOT / "data"
HISTORY_FILE = DATA_DIR / "chat_history.json"
SETTINGS_FILE = DATA_DIR / "gui_settings.json"
ERROR_LOG_FILE = DATA_DIR / "error_log.json"
current_session_id = uuid.uuid4().hex


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, value: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def _record_error(message: str, detail: str | None = None) -> None:
    entries = _read_json(ERROR_LOG_FILE, [])
    entries.insert(0, {"id": uuid.uuid4().hex, "time": datetime.now(timezone.utc).isoformat(), "message": message, "detail": detail or ""})
    _write_json(ERROR_LOG_FILE, entries[:200])


def _history_list() -> list[dict[str, Any]]:
    sessions = _read_json(HISTORY_FILE, [])
    return [{"id": item.get("id"), "title": item.get("title", "New chat"), "updated_at": item.get("updated_at", "")} for item in sessions if isinstance(item, dict)]


def _save_session() -> None:
    user_messages = []
    for item in messages:
        if item.get("role") not in {"user", "assistant"}:
            continue
        saved = dict(item)
        if isinstance(saved.get("content"), list):
            saved["content"] = "\n".join(part.get("text", "[image attached]") for part in saved["content"] if isinstance(part, dict))
        user_messages.append(saved)
    if not user_messages:
        return
    sessions = _read_json(HISTORY_FILE, [])
    raw_title = next((str(item.get("content", "")).strip() for item in user_messages if item.get("role") == "user"), "New chat")
    title = raw_title.split("\n\n[", 1)[0].strip()[:70] or "New chat"
    session = {"id": current_session_id, "title": title, "updated_at": datetime.now(timezone.utc).isoformat(), "messages": user_messages}
    sessions = [item for item in sessions if item.get("id") != current_session_id]
    sessions.insert(0, session)
    _write_json(HISTORY_FILE, sessions[:100])


def _settings() -> dict[str, str]:
    stored = _read_json(SETTINGS_FILE, {}) or {}
    return {
        "personalization": str(stored.get("personalization", "")),
        "system_prompt": str(stored.get("system_prompt", "")).strip() or SYSTEM_PROMPT,
    }


def _system_content() -> str:
    settings = _settings()
    return settings["system_prompt"] + ("\n\nPERSONALIZATION:\n" + settings["personalization"] if settings["personalization"] else "")


def emit(payload: dict[str, Any]) -> None:
    with output_lock:
        sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
        sys.stdout.flush()


class BridgeUI:
    def thinking(self, status: str) -> None:
        emit({"type": "thinking", "status": status})

    def clear_thinking(self, reset: bool = True) -> None:
        emit({"type": "thinking_end"})

    def begin_reasoning(self) -> None:
        emit({"type": "reasoning_start"})

    def stream_reasoning(self, text: str) -> None:
        emit({"type": "reasoning_token", "text": text})

    def end_reasoning(self) -> None:
        emit({"type": "reasoning_end"})

    def begin_response(self) -> None:
        emit({"type": "response_start"})

    def stream(self, text: str) -> None:
        emit({"type": "token", "text": text})

    def end_response(self) -> None:
        emit({"type": "response_end"})

    def tool(self, name: str) -> None:
        emit({"type": "tool_start", "name": name})

    def tool_complete(self) -> None:
        emit({"type": "tool_complete"})

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
    ) -> None:
        emit({
            "type": "usage",
            "prompt": prompt,
            "completion": completion,
            "total": total,
            "reasoning": reasoning,
            "elapsed": elapsed,
            "tps": tps,
            "visible_content": visible_content,
            "tool_payload": tool_payload,
        })

    def usage(self, prompt: int, completion: int, elapsed: float) -> None:
        emit({"type": "usage", "prompt": prompt, "completion": completion, "elapsed": elapsed})

    def error(self, message: str, detail: str | None = None, hint: str | None = None) -> None:
        _record_error(message, detail)
        emit({"type": "error", "message": message, "detail": detail, "hint": hint})


def confirm_action(name: str, arguments: dict[str, Any]) -> bool:
    if name in always_allowed_tools:
        return True
    permission_id = uuid.uuid4().hex
    waiter = threading.Event()
    with pending_lock:
        pending_permissions[permission_id] = {"event": waiter, "approved": False, "tool": name}

    emit({
        "type": "permission_required",
        "id": permission_id,
        "tool": name,
        "arguments": arguments,
    })

    waiter.wait()
    with pending_lock:
        result = pending_permissions.pop(permission_id, {"approved": False})
    return bool(result.get("approved"))


def create_agent(provider: str | None = None) -> Agent:
    selected = provider or current_provider
    try:
        settings = get_llm_config(selected)
    except ValueError:
        selected = "local"
        settings = get_llm_config(selected)

    return Agent(
        base_url=settings["base_url"],
        api_key=settings["api_key"],
        model=settings["model"],
        confirm_action=confirm_action,
        should_stop=cancel_request.is_set,
        ui=BridgeUI(),
    )


agent = create_agent()


def run_request(content: str | list[dict[str, Any]]) -> None:
    global request_active
    try:
        messages.append({"role": "user", "content": content})
        response = agent.process_message(messages, temperature=0.7)
        messages.append({"role": "assistant", "content": response})
        _save_session()
        emit({"type": "complete", "text": response, "session_id": current_session_id})
        emit({"type": "history_list", "items": _history_list(), "current_session_id": current_session_id})
    except Exception as error:
        _record_error("Astral mengalami kesalahan.", f"{type(error).__name__}: {error}")
        emit({"type": "error", "message": "Astral mengalami kesalahan.", "detail": f"{type(error).__name__}: {error}"})
    finally:
        cancel_request.clear()
        request_active = False


def read_commands() -> None:
    try:
        for line in sys.stdin:
            try:
                commands.put(json.loads(line))
            except json.JSONDecodeError as error:
                emit({"type": "error", "message": "Command JSON tidak valid.", "detail": str(error)})
    finally:
        commands.put({"type": "shutdown"})


def main() -> None:
    global request_active, agent, current_provider, current_session_id
    stored_settings = _read_json(SETTINGS_FILE, {}) or {}
    always_allowed_tools.update(str(item) for item in stored_settings.get("always_allowed_tools", []) if item)
    emit({"type": "bridge_ready", "provider": current_provider, "model": agent.model, "session_id": current_session_id})
    threading.Thread(target=read_commands, daemon=True).start()

    while True:
        command = commands.get()
        kind = command.get("type")

        if kind == "shutdown":
            return
        if kind == "cancel_request":
            cancel_request.set()
            with pending_lock:
                for pending in pending_permissions.values():
                    pending["approved"] = False
                    pending["event"].set()
            emit({"type": "request_cancelled"})
            continue
        if kind == "history_list":
            emit({"type": "history_list", "items": _history_list()})
            continue
        if kind == "history_load":
            requested_id = str(command.get("id", ""))
            session = next((item for item in _read_json(HISTORY_FILE, []) if item.get("id") == requested_id), None)
            if session:
                messages[:] = [{"role": "system", "content": _system_content()}, *session.get("messages", [])]
                emit({"type": "history_loaded", "id": requested_id, "messages": session.get("messages", [])})
            continue
        if kind == "memory_list":
            emit({"type": "memory_list", "items": list_memories(100)})
            continue
        if kind == "memory_save":
            try:
                if command.get("id"):
                    result = update_memory(str(command["id"]), str(command.get("content", "")), str(command.get("category", "general")), command.get("tags", []))
                else:
                    result = save_memory(str(command.get("content", "")), str(command.get("category", "general")), command.get("tags", []))
                emit({"type": "memory_saved", "result": result, "items": list_memories(100)})
            except Exception as error:
                _record_error("Memory gagal disimpan.", str(error))
                emit({"type": "error", "message": "Memory gagal disimpan.", "detail": str(error)})
            continue
        if kind == "memory_delete":
            emit({"type": "memory_deleted", "result": delete_memory(str(command.get("id", ""))), "items": list_memories(100)})
            continue
        if kind == "settings_get":
            emit({"type": "settings", "settings": _settings()})
            continue
        if kind == "settings_save":
            settings = {"personalization": str(command.get("personalization", "")), "system_prompt": str(command.get("system_prompt", "")).strip() or SYSTEM_PROMPT, "always_allowed_tools": sorted(always_allowed_tools)}
            _write_json(SETTINGS_FILE, settings)
            messages[0] = {"role": "system", "content": _system_content()}
            emit({"type": "settings", "settings": settings})
            continue
        if kind == "error_log":
            emit({"type": "error_log", "items": _read_json(ERROR_LOG_FILE, [])})
            continue
        if kind == "permission_result":
            permission_id = str(command.get("id", ""))
            with pending_lock:
                pending = pending_permissions.get(permission_id)
                if pending:
                    pending["approved"] = bool(command.get("approved"))
                    if command.get("always") and pending["approved"]:
                        always_allowed_tools.add(str(pending.get("tool", "")))
                        stored_settings = _read_json(SETTINGS_FILE, {}) or {}
                        stored_settings["always_allowed_tools"] = sorted(always_allowed_tools)
                        _write_json(SETTINGS_FILE, stored_settings)
                    pending["event"].set()
            continue
        if kind == "new_chat":
            current_session_id = uuid.uuid4().hex
            messages[:] = [{"role": "system", "content": _system_content()}]
            emit({"type": "session_reset", "session_id": current_session_id})
            continue
        if kind == "set_provider":
            if request_active:
                emit({"type": "busy"})
                continue
            requested = str(command.get("provider", "local")).strip().lower()
            try:
                agent = create_agent(requested)
                current_provider = requested
                emit({"type": "provider_changed", "provider": current_provider, "model": agent.model})
            except Exception as error:
                emit({"type": "error", "message": "Provider tidak dapat dipilih.", "detail": f"{type(error).__name__}: {error}"})
            continue
        if kind == "user_message":
            if request_active:
                emit({"type": "busy"})
                continue
            text = str(command.get("text", "")).strip()
            attachments = command.get("attachments", [])
            if not text and not attachments:
                continue
            image_parts = []
            if attachments:
                attachment_context = []
                for item in attachments:
                    name = item.get("name", "file")
                    if item.get("kind") == "file" and item.get("content"):
                        attachment_context.append(f"\n--- File: {name} ---\n{item['content']}")
                    elif item.get("kind") == "screenshot":
                        image_parts.append({"type": "image_url", "image_url": {"url": item.get("content", "")}})
                        attachment_context.append(f"[Image attached: {name}]")
                    else:
                        attachment_context.append(f"[Attachment: {name}]")
                text += "\n\n" + "\n".join(attachment_context)
            request_active = True
            cancel_request.clear()
            content = [{"type": "text", "text": text}, *image_parts] if image_parts else text
            threading.Thread(target=run_request, args=(content,), daemon=True).start()


if __name__ == "__main__":
    main()
