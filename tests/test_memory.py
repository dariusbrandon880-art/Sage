"""Tests for SAGE memory layer."""

from sage.memory import MemoryStore


class TestMemoryStore:
    """Test cases for MemoryStore."""

    def test_memory_store_initialization(self):
        """Test memory store initializes correctly."""
        store = MemoryStore()
        assert store is not None
        assert len(store.sessions) == 0

    def test_create_session(self):
        """Test creating a session."""
        store = MemoryStore()
        store.create_session("session_1", {"user_id": "user_1"})

        session = store.get_session("session_1")
        assert session is not None
        assert session["metadata"]["user_id"] == "user_1"

    def test_store_and_retrieve_context(self):
        """Test storing and retrieving context."""
        store = MemoryStore()
        store.store_context("key_1", "value_1")

        value = store.get_context("key_1")
        assert value == "value_1"

    def test_get_nonexistent_session(self):
        """Test retrieving nonexistent session."""
        store = MemoryStore()
        session = store.get_session("nonexistent")
        assert session is None
