from tools import memory


def test_memory_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setattr(memory, "MEMORY_FILE", tmp_path / "memory.json")
    saved = memory.save_memory("Bos suka jawaban singkat.", "preference", ["style"])
    assert memory.search_memories("jawaban")[0]["id"] == saved["id"]
    assert memory.delete_memory(saved["id"])["success"]
    assert not memory.search_memories("jawaban")
