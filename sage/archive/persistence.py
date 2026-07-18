"""Persistent storage backend for archive layer."""

from typing import Optional, List
from pathlib import Path
import json
from datetime import datetime
from sage.archive.models import ArchiveEvent, EventLog, EventQuery


class PersistentArchiveStore:
    """File-based persistent storage for archive events."""

    def __init__(self, storage_path: str = ".sage/archive"):
        """Initialize persistent archive store.
        
        Args:
            storage_path: Root path for storing archive files.
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session's event log."""
        return self.storage_path / f"{session_id}.json"

    def save_event_log(self, event_log: EventLog) -> None:
        """Persist an event log to storage.
        
        Args:
            event_log: EventLog object to save.
        """
        session_path = self._get_session_path(event_log.session_id)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        data = {
            "session_id": event_log.session_id,
            "events": [
                {
                    "id": event.id,
                    "session_id": event.session_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                    "metadata": event.metadata,
                    "source": event.source,
                }
                for event in event_log.events
            ],
            "created_at": event_log.created_at.isoformat(),
            "updated_at": event_log.updated_at.isoformat(),
        }
        
        with open(session_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_event_log(self, session_id: str) -> Optional[EventLog]:
        """Load an event log from storage.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            EventLog object or None if not found.
        """
        session_path = self._get_session_path(session_id)
        
        if not session_path.exists():
            return None
        
        with open(session_path, "r") as f:
            data = json.load(f)
        
        events = [
            ArchiveEvent(
                id=event["id"],
                session_id=event["session_id"],
                event_type=event["event_type"],
                timestamp=datetime.fromisoformat(event["timestamp"]),
                data=event["data"],
                metadata=event["metadata"],
                source=event["source"],
            )
            for event in data["events"]
        ]
        
        return EventLog(
            session_id=data["session_id"],
            events=events,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def delete_event_log(self, session_id: str) -> bool:
        """Delete an event log from storage.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            True if deleted, False if not found.
        """
        session_path = self._get_session_path(session_id)
        
        if session_path.exists():
            session_path.unlink()
            return True
        return False

    def list_sessions(self) -> List[str]:
        """List all stored session IDs.
        
        Returns:
            List of session identifiers.
        """
        return [
            f.stem 
            for f in self.storage_path.glob("*.json")
        ]

    def query(self, query: EventQuery) -> List[ArchiveEvent]:
        """Retrieve events matching a query.
        
        Args:
            query: EventQuery object.
            
        Returns:
            List of matching ArchiveEvent objects.
        """
        event_log = self.load_event_log(query.session_id)
        if not event_log:
            return []
        
        results = event_log.events
        
        # Filter by event types if specified
        if query.event_types:
            results = [
                e for e in results 
                if e.event_type in query.event_types
            ]
        
        # Filter by time range if specified
        if query.start_time:
            results = [e for e in results if e.timestamp >= query.start_time]
        if query.end_time:
            results = [e for e in results if e.timestamp <= query.end_time]
        
        # Apply pagination
        total = len(results)
        results = results[query.offset:query.offset + query.limit]
        
        return results

    def export_session_timeline(self, session_id: str) -> List[dict]:
        """Export a session's events as a timeline.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            List of timeline entries (dict format).
        """
        event_log = self.load_event_log(session_id)
        if not event_log:
            return []
        
        # Sort by timestamp
        sorted_events = sorted(event_log.events, key=lambda e: e.timestamp)
        
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "type": event.event_type,
                "source": event.source,
                "data": event.data,
            }
            for event in sorted_events
        ]
