"""Tests for persistent memory storage."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from sage.memory.models import MemoryEntry, SessionMemory, RetrievalQuery
from sage.memory.persistence import PersistentMemoryStore


class TestPersistentMemoryStore:
    """Test cases for PersistentMemoryStore."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def store(self, temp_storage):
        """Create a store instance with temporary storage."""
        return PersistentMemoryStore(storage_path=temp_storage)

    def test_store_initialization(self, temp_storage):
        """Test store initializes with correct path."""
        store = PersistentMemoryStore(storage_path=temp_storage)
        assert store.storage_path == Path(temp_storage)
        assert store.storage_path.exists()

    def test_save_and_load_session(self, store):
        """Test saving and loading a session."""
        session = SessionMemory(session_id="test_session_1")
        session.add_entry("key_1", "value_1")
        session.add_entry("key_2", {"nested": "data"})
        
        store.save_session(session)
        
        loaded = store.load_session("test_session_1")
        assert loaded is not None
        assert loaded.session_id == "test_session_1"
        assert len(loaded.entries) == 2
        assert loaded.get_entry("key_1").value == "value_1"
        assert loaded.get_entry("key_2").value == {"nested": "data"}

    def test_load_nonexistent_session(self, store):
        """Test loading a session that doesn't exist."""
        loaded = store.load_session("nonexistent")
        assert loaded is None

    def test_delete_session(self, store):
        """Test deleting a session."""
        session = SessionMemory(session_id="test_session_2")
        session.add_entry("key_1", "value_1")
        
        store.save_session(session)
        assert store.load_session("test_session_2") is not None
        
        deleted = store.delete_session("test_session_2")
        assert deleted is True
        assert store.load_session("test_session_2") is None

    def test_delete_nonexistent_session(self, store):
        """Test deleting a session that doesn't exist."""
        deleted = store.delete_session("nonexistent")
        assert deleted is False

    def test_list_sessions(self, store):
        """Test listing all sessions."""
        for i in range(3):
            session = SessionMemory(session_id=f"session_{i}")
            session.add_entry("key", f"value_{i}")
            store.save_session(session)
        
        sessions = store.list_sessions()
        assert len(sessions) == 3
        assert "session_0" in sessions
        assert "session_1" in sessions
        assert "session_2" in sessions

    def test_query_by_key(self, store):
        """Test querying entries by key."""
        session = SessionMemory(session_id="query_test")
        session.add_entry("target_key", "target_value")
        session.add_entry("other_key", "other_value")
        store.save_session(session)
        
        query = RetrievalQuery(session_id="query_test", key="target_key")
        results = store.query(query)
        
        assert len(results) == 1
        assert results[0].key == "target_key"
        assert results[0].value == "target_value"

    def test_query_by_time_range(self, store):
        """Test querying entries by time range."""
        session = SessionMemory(session_id="time_test")
        
        now = datetime.now()
        entry1 = session.add_entry("key_1", "value_1")
        entry1.created_at = now - timedelta(hours=2)
        
        entry2 = session.add_entry("key_2", "value_2")
        entry2.created_at = now - timedelta(hours=1)
        
        entry3 = session.add_entry("key_3", "value_3")
        entry3.created_at = now
        
        store.save_session(session)
        
        start = now - timedelta(hours=1, minutes=30)
        end = now
        query = RetrievalQuery(
            session_id="time_test",
            start_time=start,
            end_time=end,
        )
        results = store.query(query)
        
        assert len(results) == 2
        assert any(r.key == "key_2" for r in results)
        assert any(r.key == "key_3" for r in results)

    def test_query_by_metadata(self, store):
        """Test querying entries by metadata filters."""
        session = SessionMemory(session_id="metadata_test")
        
        entry1 = session.add_entry("key_1", "value_1")
        entry1.metadata = {"priority": "high", "category": "urgent"}
        
        entry2 = session.add_entry("key_2", "value_2")
        entry2.metadata = {"priority": "low", "category": "general"}
        
        store.save_session(session)
        
        query = RetrievalQuery(
            session_id="metadata_test",
            metadata_filters={"priority": "high"},
        )
        results = store.query(query)
        
        assert len(results) == 1
        assert results[0].key == "key_1"

    def test_persistence_across_instances(self, temp_storage):
        """Test that data persists across store instances."""
        store1 = PersistentMemoryStore(storage_path=temp_storage)
        session = SessionMemory(session_id="persistent_test")
        session.add_entry("key_1", "value_1")
        store1.save_session(session)
        
        # Create new store instance and verify data
        store2 = PersistentMemoryStore(storage_path=temp_storage)
        loaded = store2.load_session("persistent_test")
        
        assert loaded is not None
        assert len(loaded.entries) == 1
        assert loaded.get_entry("key_1").value == "value_1"
