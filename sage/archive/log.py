"""Archive logging system for SAGE operations history."""

from typing import List, Dict, Any, Optional
from datetime import datetime
from sage.archive.models import EventLog, ArchiveEvent, EventQuery
from sage.archive.persistence import PersistentArchiveStore


class ArchiveLog:
    """Archive for historical logging and retrieval of SAGE operations."""

    def __init__(self, session_id: str = "default", persistent_path: Optional[str] = None, use_persistence: bool = True):
        """Initialize archive log.
        
        Args:
            session_id: Session identifier for this archive.
            persistent_path: Path for persistent storage. Defaults to .sage/archive
            use_persistence: Whether to use persistent storage backend.
        """
        self.session_id = session_id
        self.events: List[Dict[str, Any]] = []
        self.use_persistence = use_persistence
        self.persistent_store = (
            PersistentArchiveStore(storage_path=persistent_path or ".sage/archive")
            if use_persistence
            else None
        )
        event_log = None
        
        # Load existing event log if available
        if self.use_persistence and self.persistent_store:
            event_log = self.persistent_store.load_event_log(session_id)
        
        if event_log is None:
            event_log = EventLog(session_id=session_id)

        self.event_log: EventLog = event_log

    def log_event(self, event_type: str, data: Dict[str, Any], source: str = "archive") -> None:
        """Log an event to archive.
        
        Args:
            event_type: Type of event being logged.
            data: Event data dictionary.
            source: Source of the event (default: "archive").
        """
        # Add to model-based event log
        self.event_log.add_event(event_type, data, source=source)
        
        # Also maintain legacy format for backward compatibility
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
            "source": source,
        }
        self.events.append(entry)
        
        # Persist to disk if enabled
        if self.use_persistence and self.persistent_store:
            self.persistent_store.save_event_log(self.event_log)

    def get_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve events from archive.
        
        Args:
            event_type: Optional filter by event type.
            
        Returns:
            List of matching events in legacy format.
        """
        if event_type:
            return [e for e in self.events if e["type"] == event_type]
        return self.events

    def get_events_by_type(self, event_type: str) -> List[ArchiveEvent]:
        """Retrieve events of a specific type.
        
        Args:
            event_type: Type of events to retrieve.
            
        Returns:
            List of ArchiveEvent objects.
        """
        return self.event_log.get_events_by_type(event_type)

    def get_events_in_range(self, start_time: datetime, end_time: datetime) -> List[ArchiveEvent]:
        """Retrieve events within a time range.
        
        Args:
            start_time: Start of time range.
            end_time: End of time range.
            
        Returns:
            List of ArchiveEvent objects.
        """
        return self.event_log.get_events_in_range(start_time, end_time)

    def get_latest_event(self, event_type: Optional[str] = None) -> Optional[ArchiveEvent]:
        """Get the most recent event.
        
        Args:
            event_type: Optional filter by event type.
            
        Returns:
            Latest ArchiveEvent or None if no events.
        """
        return self.event_log.get_latest_event(event_type)

    def query_events(self, event_types: Optional[List[str]] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[ArchiveEvent]:
        """Query events with multiple filters.
        
        Args:
            event_types: List of event types to retrieve.
            start_time: Start of time range.
            end_time: End of time range.
            
        Returns:
            List of matching ArchiveEvent objects.
        """
        if self.use_persistence and self.persistent_store:
            query = EventQuery(
                session_id=self.session_id,
                event_types=event_types or [],
                start_time=start_time,
                end_time=end_time,
            )
            return self.persistent_store.query(query)
        
        return []

    def export_timeline(self) -> List[dict]:
        """Export events as a chronological timeline.
        
        Returns:
            List of timeline entries.
        """
        if self.use_persistence and self.persistent_store:
            return self.persistent_store.export_session_timeline(self.session_id)
        
        return []

    def clear(self) -> None:
        """Clear all events from archive."""
        self.events.clear()
        self.event_log = EventLog(session_id=self.session_id)
        
        if self.use_persistence and self.persistent_store:
            self.persistent_store.delete_event_log(self.session_id)

    def save(self) -> bool:
        """Persist the current event log to storage.
        
        Returns:
            True if saved successfully, False otherwise.
        """
        if self.use_persistence and self.persistent_store:
            self.persistent_store.save_event_log(self.event_log)
            return True
        return False

    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the session's activity.
        
        Returns:
            Dictionary with session statistics.
        """
        return {
            "session_id": self.session_id,
            "total_events": len(self.event_log.events),
            "event_types": list(set(e.event_type for e in self.event_log.events)),
            "created_at": self.event_log.created_at.isoformat(),
            "updated_at": self.event_log.updated_at.isoformat(),
            "timeline": self.export_timeline(),
        }
