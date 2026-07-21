"""Persistent storage backend for memory layer."""

from typing import Optional, List
from pathlib import Path
import json
from datetime import datetime
from sage.memory.models import MemoryEntry, SessionMemory, RetrievalQuery


class PersistentMemoryStore:
    """File-based persistent storage for memory entries."""

    def __init__(self, storage_path: str = ".sage/memory"):
        """Initialize persistent memory store.
        
        Args:
            storage_path: Root path for storing memory files.
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.storage_path / f"{session_id}.json"

    def save_session(self, session_memory: SessionMemory) -> None:
        """Persist a session's memory to storage.
        
        Args:
            session_memory: SessionMemory object to save.
        """
        session_path = self._get_session_path(session_memory.session_id)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to JSON-serializable format
        data = {
            "session_id": session_memory.session_id,
            "entries": [
                {
                    "id": entry.id,
                    "session_id": entry.session_id,
                    "key": entry.key,
                    "value": entry.value,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                    "metadata": entry.metadata,
                }
                for entry in session_memory.entries
            ],
            "created_at": session_memory.created_at.isoformat(),
            "updated_at": session_memory.updated_at.isoformat(),
        }
        
        with open(session_path, "w") as f:
            json.dump(data, f, indent=2)

    def load_session(self, session_id: str) -> Optional[SessionMemory]:
        """Load a session's memory from storage.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            SessionMemory object or None if not found.
        """
        session_path = self._get_session_path(session_id)
        
        if not session_path.exists():
            return None
        
        with open(session_path, "r") as f:
            data = json.load(f)
        
        entries = [
            MemoryEntry(
                id=entry["id"],
                session_id=entry["session_id"],
                key=entry["key"],
                value=entry["value"],
                created_at=datetime.fromisoformat(entry["created_at"]),
                updated_at=datetime.fromisoformat(entry["updated_at"]),
                metadata=entry["metadata"],
            )
            for entry in data["entries"]
        ]
        
        return SessionMemory(
            session_id=data["session_id"],
            entries=entries,
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )

    def delete_session(self, session_id: str) -> bool:
        """Delete a session's memory from storage.
        
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

    def query(self, query: RetrievalQuery) -> List[MemoryEntry]:
        """Retrieve memory entries matching a query.
        
        Args:
            query: RetrievalQuery object.
            
        Returns:
            List of matching MemoryEntry objects.
        """
        session = self.load_session(query.session_id)
        if not session:
            return []
        
        results = session.entries
        
        # Filter by key if specified
        if query.key:
            results = [e for e in results if e.key == query.key]
        
        # Filter by time range if specified
        if query.start_time:
            results = [e for e in results if e.created_at >= query.start_time]
        if query.end_time:
            results = [e for e in results if e.created_at <= query.end_time]
        
        # Filter by metadata if specified
        for meta_key, meta_value in query.metadata_filters.items():
            results = [
                e for e in results 
                if e.metadata.get(meta_key) == meta_value
            ]
        
        return results
