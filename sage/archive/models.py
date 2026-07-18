"""Archive event models for SAGE history tracking."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ArchiveEvent(BaseModel):
    """A single event in the archive."""
    
    id: str
    session_id: str
    event_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: str = "unknown"


class EventLog(BaseModel):
    """Collection of events for a session."""
    
    session_id: str
    events: List[ArchiveEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def add_event(
        self, 
        event_type: str, 
        data: Dict[str, Any],
        source: str = "unknown",
        event_id: Optional[str] = None,
    ) -> ArchiveEvent:
        """Add an event to the log."""
        event = ArchiveEvent(
            id=event_id or f"{self.session_id}_{event_type}_{len(self.events)}",
            session_id=self.session_id,
            event_type=event_type,
            data=data,
            source=source,
        )
        self.events.append(event)
        self.updated_at = datetime.now()
        return event
    
    def get_events_by_type(self, event_type: str) -> List[ArchiveEvent]:
        """Retrieve events by type."""
        return [e for e in self.events if e.event_type == event_type]
    
    def get_events_in_range(
        self, 
        start_time: datetime, 
        end_time: datetime,
    ) -> List[ArchiveEvent]:
        """Retrieve events within a time range."""
        return [
            e for e in self.events 
            if start_time <= e.timestamp <= end_time
        ]
    
    def get_latest_event(self, event_type: Optional[str] = None) -> Optional[ArchiveEvent]:
        """Get the most recent event, optionally filtered by type."""
        filtered = (
            self.get_events_by_type(event_type) 
            if event_type 
            else self.events
        )
        return max(filtered, key=lambda e: e.timestamp) if filtered else None


class EventQuery(BaseModel):
    """Query structure for event retrieval."""
    
    session_id: str
    event_types: List[str] = Field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
