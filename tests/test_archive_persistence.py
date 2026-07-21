"""Tests for persistent archive storage."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from sage.archive.models import EventLog, EventQuery
from sage.archive.persistence import PersistentArchiveStore


class TestPersistentArchiveStore:
    """Test cases for PersistentArchiveStore."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary storage directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def store(self, temp_storage):
        """Create a store instance with temporary storage."""
        return PersistentArchiveStore(storage_path=temp_storage)

    def test_store_initialization(self, temp_storage):
        """Test store initializes with correct path."""
        store = PersistentArchiveStore(storage_path=temp_storage)
        assert store.storage_path == Path(temp_storage)
        assert store.storage_path.exists()

    def test_save_and_load_event_log(self, store):
        """Test saving and loading an event log."""
        log = EventLog(session_id="test_session_1")
        log.add_event("session_start", {"user": "test_user"}, source="runtime")
        log.add_event("memory_update", {"key": "test", "value": "data"}, source="memory")

        store.save_event_log(log)

        loaded = store.load_event_log("test_session_1")
        assert loaded is not None
        assert loaded.session_id == "test_session_1"
        assert len(loaded.events) == 2
        assert loaded.events[0].event_type == "session_start"
        assert loaded.events[1].event_type == "memory_update"

    def test_load_nonexistent_log(self, store):
        """Test loading a log that doesn't exist."""
        loaded = store.load_event_log("nonexistent")
        assert loaded is None

    def test_delete_event_log(self, store):
        """Test deleting an event log."""
        log = EventLog(session_id="test_session_2")
        log.add_event("test_event", {"data": "test"})

        store.save_event_log(log)
        assert store.load_event_log("test_session_2") is not None

        deleted = store.delete_event_log("test_session_2")
        assert deleted is True
        assert store.load_event_log("test_session_2") is None

    def test_delete_nonexistent_log(self, store):
        """Test deleting a log that doesn't exist."""
        deleted = store.delete_event_log("nonexistent")
        assert deleted is False

    def test_list_sessions(self, store):
        """Test listing all stored sessions."""
        for i in range(3):
            log = EventLog(session_id=f"session_{i}")
            log.add_event("test_event", {"index": i})
            store.save_event_log(log)

        sessions = store.list_sessions()
        assert len(sessions) == 3
        assert "session_0" in sessions
        assert "session_1" in sessions
        assert "session_2" in sessions

    def test_query_by_event_type(self, store):
        """Test querying events by type."""
        log = EventLog(session_id="query_test")
        log.add_event("start", {"timestamp": "now"})
        log.add_event("update", {"data": "changed"})
        log.add_event("start", {"checkpoint": 1})
        store.save_event_log(log)

        query = EventQuery(session_id="query_test", event_types=["start"])
        results = store.query(query)

        assert len(results) == 2
        assert all(e.event_type == "start" for e in results)

    def test_query_by_time_range(self, store):
        """Test querying events by time range."""
        log = EventLog(session_id="time_test")

        now = datetime.now()
        event1 = log.add_event("event_1", {}, source="test")
        event1.timestamp = now - timedelta(hours=2)

        event2 = log.add_event("event_2", {}, source="test")
        event2.timestamp = now - timedelta(hours=1)

        event3 = log.add_event("event_3", {}, source="test")
        event3.timestamp = now

        store.save_event_log(log)

        start = now - timedelta(hours=1, minutes=30)
        end = now
        query = EventQuery(
            session_id="time_test",
            start_time=start,
            end_time=end,
        )
        results = store.query(query)

        assert len(results) == 2

    def test_query_pagination(self, store):
        """Test query pagination."""
        log = EventLog(session_id="pagination_test")
        for i in range(10):
            log.add_event(f"event_{i}", {"index": i})
        store.save_event_log(log)

        query = EventQuery(
            session_id="pagination_test",
            limit=5,
            offset=0,
        )
        results1 = store.query(query)
        assert len(results1) == 5

        query.offset = 5
        results2 = store.query(query)
        assert len(results2) == 5

    def test_export_session_timeline(self, store):
        """Test exporting a session's timeline."""
        log = EventLog(session_id="timeline_test")

        now = datetime.now()
        event1 = log.add_event("start", {"phase": 1}, source="runtime")
        event1.timestamp = now

        event2 = log.add_event("process", {"status": "running"}, source="acr")
        event2.timestamp = now + timedelta(seconds=1)

        event3 = log.add_event("complete", {"result": "success"}, source="runtime")
        event3.timestamp = now + timedelta(seconds=2)

        store.save_event_log(log)

        timeline = store.export_session_timeline("timeline_test")
        assert len(timeline) == 3
        assert timeline[0]["type"] == "start"
        assert timeline[1]["type"] == "process"
        assert timeline[2]["type"] == "complete"
        # Verify chronological order
        assert timeline[0]["timestamp"] < timeline[1]["timestamp"] < timeline[2]["timestamp"]

    def test_multiple_event_types_query(self, store):
        """Test querying multiple event types."""
        log = EventLog(session_id="multi_type_test")
        log.add_event("start", {})
        log.add_event("update", {})
        log.add_event("checkpoint", {})
        log.add_event("stop", {})
        store.save_event_log(log)

        query = EventQuery(
            session_id="multi_type_test",
            event_types=["start", "checkpoint", "stop"],
        )
        results = store.query(query)

        assert len(results) == 3
        types = {e.event_type for e in results}
        assert types == {"start", "checkpoint", "stop"}

    def test_persistence_across_instances(self, temp_storage):
        """Test that data persists across store instances."""
        store1 = PersistentArchiveStore(storage_path=temp_storage)
        log = EventLog(session_id="persistent_test")
        log.add_event("test_event", {"data": "test"}, source="test")
        store1.save_event_log(log)

        # Create new store instance and verify data
        store2 = PersistentArchiveStore(storage_path=temp_storage)
        loaded = store2.load_event_log("persistent_test")

        assert loaded is not None
        assert len(loaded.events) == 1
        assert loaded.events[0].event_type == "test_event"
