"""Memory models for SAGE persistence."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MemoryEntry(BaseModel):
    """A single entry in memory storage."""

    id: str
    session_id: str
    key: str
    value: Any
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionMemory(BaseModel):
    """Complete memory context for a session."""

    session_id: str
    entries: List[MemoryEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def __getitem__(self, key: str) -> Any:
        """Allow dict-like indexing to retrieve entry values."""
        entry = self.get_entry(key)
        if entry is None:
            raise KeyError(key)
        return entry.value

    def add_entry(self, key: str, value: Any, entry_id: Optional[str] = None) -> MemoryEntry:
        """Add an entry to session memory."""
        entry = MemoryEntry(
            id=entry_id or f"{self.session_id}_{len(self.entries)}",
            session_id=self.session_id,
            key=key,
            value=value,
        )
        self.entries.append(entry)
        self.updated_at = datetime.now()
        return entry

    def get_entry(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve an entry by key."""
        for entry in self.entries:
            if entry.key == key:
                return entry
        return None

    def update_entry(self, key: str, value: Any) -> Optional[MemoryEntry]:
        """Update an entry by key."""
        for entry in self.entries:
            if entry.key == key:
                entry.value = value
                entry.updated_at = datetime.now()
                self.updated_at = datetime.now()
                return entry
        return None


class RetrievalQuery(BaseModel):
    """Query structure for memory retrieval."""

    session_id: str
    key: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
