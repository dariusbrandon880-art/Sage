"""Archive logging system for SAGE operations history."""

from typing import List, Dict, Any
from datetime import datetime


class ArchiveLog:
    """Archive for historical logging and retrieval of SAGE operations."""

    def __init__(self):
        """Initialize archive log."""
        self.events: List[Dict[str, Any]] = []

    def log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log an event to archive.
        
        Args:
            event_type: Type of event being logged.
            data: Event data dictionary.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "data": data,
        }
        self.events.append(entry)

    def get_events(self, event_type: str = None) -> List[Dict[str, Any]]:
        """Retrieve events from archive.
        
        Args:
            event_type: Optional filter by event type.
            
        Returns:
            List of matching events.
        """
        if event_type:
            return [e for e in self.events if e["type"] == event_type]
        return self.events

    def clear(self) -> None:
        """Clear all events from archive."""
        self.events.clear()
