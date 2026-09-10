"""Persistent local long-term memory."""
import json
import threading
from datetime import datetime, timezone
from uuid import uuid4
from config import MAX_MEMORY_ENTRIES, MEMORY_FILE

_LOCK = threading.Lock()

def _load():
    if not MEMORY_FILE.exists(): return []
    try: data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error: raise RuntimeError(f"Memory tidak dapat dibaca: {error}") from error
    if not isinstance(data, list): raise RuntimeError("Format memory harus JSON array.")
    return [x for x in data if isinstance(x, dict)]

def _save(entries):
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = MEMORY_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(MEMORY_FILE)

def save_memory(content, category="general", tags=None):
    if not isinstance(content, str) or not content.strip() or len(content) > 4000: raise ValueError("content harus berupa string 1-4000 karakter.")
    if not isinstance(category, str) or not category.strip(): raise ValueError("category harus string non-kosong.")
    if tags is None: tags = []
    if not isinstance(tags, list) or any(not isinstance(x, str) for x in tags): raise ValueError("tags harus array string.")
    now = datetime.now(timezone.utc).isoformat(); content = content.strip()
    with _LOCK:
        entries = _load()
        for entry in entries:
            if entry.get("content", "").casefold() == content.casefold():
                entry.update({"category": category.strip(), "tags": sorted(set(x.strip().lower() for x in tags if x.strip()))[:20], "updated_at": now}); _save(entries); return {"success": True, "id": entry["id"], "updated": True}
        if len(entries) >= MAX_MEMORY_ENTRIES: raise RuntimeError("Batas memory tercapai.")
        entry = {"id": uuid4().hex, "content": content, "category": category.strip(), "tags": sorted(set(x.strip().lower() for x in tags if x.strip()))[:20], "created_at": now, "updated_at": now}
        entries.append(entry); _save(entries)
    return {"success": True, "id": entry["id"], "updated": False}

def search_memories(query, limit=5):
    if not isinstance(query, str) or not query.strip(): return []
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20: raise ValueError("limit harus 1-20.")
    terms = {x.casefold() for x in query.split() if len(x) >= 2}
    with _LOCK: entries = _load()
    def score(entry):
        text = (str(entry.get("content", "")) + " " + str(entry.get("category", "")) + " " + " ".join(entry.get("tags", []))).casefold()
        return sum(term in text for term in terms)
    return sorted((x for x in entries if score(x)), key=lambda x: (score(x), x.get("updated_at", "")), reverse=True)[:limit]

def list_memories(limit=20):
    with _LOCK: return sorted(_load(), key=lambda x: x.get("updated_at", ""), reverse=True)[:limit]

def delete_memory(memory_id):
    with _LOCK:
        entries = _load(); new = [x for x in entries if x.get("id") != memory_id]
        if len(new) == len(entries): return {"success": False, "error": "Memori tidak ditemukan."}
        _save(new)
    return {"success": True, "id": memory_id}

def update_memory(memory_id, content, category="general", tags=None):
    if not isinstance(memory_id, str) or not memory_id.strip():
        raise ValueError("memory_id harus string non-kosong.")
    if not isinstance(content, str) or not content.strip() or len(content) > 4000:
        raise ValueError("content harus berupa string 1-4000 karakter.")
    if tags is None: tags = []
    if not isinstance(tags, list) or any(not isinstance(x, str) for x in tags):
        raise ValueError("tags harus array string.")
    now = datetime.now(timezone.utc).isoformat()
    with _LOCK:
        entries = _load()
        entry = next((item for item in entries if item.get("id") == memory_id), None)
        if entry is None:
            return {"success": False, "error": "Memori tidak ditemukan."}
        entry.update({
            "content": content.strip(),
            "category": str(category).strip() or "general",
            "tags": sorted(set(x.strip().lower() for x in tags if x.strip()))[:20],
            "updated_at": now,
        })
        _save(entries)
    return {"success": True, "id": memory_id, "updated": True}
