"""Tests for SAGE archive layer."""

from sage.archive import ArchiveLog


class TestArchiveLog:
    """Test cases for ArchiveLog."""

    def test_archive_initialization(self):
        """Test archive initializes correctly."""
        archive = ArchiveLog()
        assert archive is not None
        assert len(archive.events) == 0

    def test_log_event(self):
        """Test logging an event."""
        archive = ArchiveLog()
        archive.log_event("test_event", {"data": "test_data"})
        
        events = archive.get_events()
        assert len(events) == 1
        assert events[0]["type"] == "test_event"
        assert events[0]["data"]["data"] == "test_data"

    def test_filter_events_by_type(self):
        """Test filtering events by type."""
        archive = ArchiveLog()
        archive.log_event("type_a", {"data": "a"})
        archive.log_event("type_b", {"data": "b"})
        archive.log_event("type_a", {"data": "a2"})
        
        type_a_events = archive.get_events("type_a")
        assert len(type_a_events) == 2
        assert all(e["type"] == "type_a" for e in type_a_events)

    def test_clear_archive(self):
        """Test clearing archive."""
        archive = ArchiveLog()
        archive.log_event("test_event", {"data": "test"})
        assert len(archive.events) == 1
        
        archive.clear()
        assert len(archive.events) == 0
