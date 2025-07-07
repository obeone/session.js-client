
from session_py_client.storage import InMemoryStorage, Storage


def test_in_memory_storage_basic():
    storage = InMemoryStorage()

    assert isinstance(storage, Storage)
    assert storage.get("a") is None
    assert not storage.has("a")

    storage.set("a", "1")
    assert storage.get("a") == "1"
    assert storage.has("a")

    storage.delete("a")
    assert storage.get("a") is None
    assert not storage.has("a")

