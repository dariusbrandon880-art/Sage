"""Memory storage for session, context, and memory object persistence."""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from sage.models import MemoryObject
from sage.memory.models import SessionMemory, RetrievalQuery
from sage.memory.persistence import PersistentMemoryStore


class MemoryStore:
    """Unified memory storage with in-memory and persistent backends."""

    def __init__(self, persistent_path: Optional[str] = None, use_persistence: bool = True):
        """Initialize memory store.
        
        Args:
            persistent_path: Path for persistent storage. Defaults to .sage/memory
            use_persistence: Whether to use persistent storage backend.
        """
        self.sessions: Dict[str, SessionMemory] = {}
        self.context: Dict[str, Any] = {}
        self.objects: Dict[str, MemoryObject] = {}
        self.use_persistence = use_persistence

        self.persistent_store = (
            PersistentMemoryStore(storage_path=persistent_path or ".sage/memory")
            if use_persistence
            else None
        )

        if self.use_persistence:
            self.objects_path = Path(persistent_path or ".sage/memory") / "objects"
            self.objects_path.mkdir(parents=True, exist_ok=True)
            self._load_all_objects()

    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> SessionMemory:
        """Create a new session in memory.
        
        Args:
            session_id: Unique session identifier.
            metadata: Optional session metadata.
            
        Returns:
            Created SessionMemory object.
        """
        session = SessionMemory(session_id=session_id)
        if metadata:
            session.add_entry("metadata", metadata)
        
        self.sessions[session_id] = session
        
        # Persist to disk if enabled
        if self.use_persistence and self.persistent_store:
            self.persistent_store.save_session(session)
        
        return session

    def get_session(self, session_id: str) -> Optional[SessionMemory]:
        """Retrieve session data.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            SessionMemory object or None if not found.
        """
        # Check in-memory first
        if session_id in self.sessions:
            return self.sessions[session_id]
        
        # Load from persistent storage if available
        if self.use_persistence and self.persistent_store:
            session = self.persistent_store.load_session(session_id)
            if session:
                self.sessions[session_id] = session
                return session
        
        return None

    def store_context(self, key: str, value: Any) -> None:
        """Store context data.
        
        Args:
            key: Context key.
            value: Context value.
        """
        self.context[key] = value

    def get_context(self, key: str) -> Optional[Any]:
        """Retrieve context data.
        
        Args:
            key: Context key.
            
        Returns:
            Context value or None if not found.
        """
        return self.context.get(key)

    def save_session(self, session_id: str) -> bool:
        """Persist a session to storage.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            True if saved successfully, False otherwise.
        """
        session = self.sessions.get(session_id)
        if not session:
            return False
        
        if self.use_persistence and self.persistent_store:
            self.persistent_store.save_session(session)
            return True
        
        return False

    def add_memory_entry(self, session_id: str, key: str, value: Any) -> bool:
        """Add a memory entry to a session.
        
        Args:
            session_id: Session identifier.
            key: Entry key.
            value: Entry value.
            
        Returns:
            True if added successfully, False otherwise.
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.add_entry(key, value)
        return self.save_session(session_id)

    def get_memory_entry(self, session_id: str, key: str) -> Optional[Any]:
        """Retrieve a memory entry from a session.
        
        Args:
            session_id: Session identifier.
            key: Entry key.
            
        Returns:
            Entry value or None if not found.
        """
        session = self.get_session(session_id)
        if not session:
            return None
        
        entry = session.get_entry(key)
        return entry.value if entry else None

    def update_memory_entry(self, session_id: str, key: str, value: Any) -> bool:
        """Update a memory entry in a session.
        
        Args:
            session_id: Session identifier.
            key: Entry key.
            value: New value.
            
        Returns:
            True if updated successfully, False otherwise.
        """
        session = self.get_session(session_id)
        if not session:
            return False
        
        updated = session.update_entry(key, value)
        if updated:
            return self.save_session(session_id)
        return False

    def query_memory(self, query: RetrievalQuery) -> List[Any]:
        """Query memory entries using a retrieval query.
        
        Args:
            query: RetrievalQuery object.
            
        Returns:
            List of matching entry values.
        """
        if self.use_persistence and self.persistent_store:
            results = self.persistent_store.query(query)
            return [r.value for r in results]
        
        return []

    def list_sessions(self) -> List[str]:
        """List all session IDs.
        
        Returns:
            List of session identifiers.
        """
        if self.use_persistence and self.persistent_store:
            return self.persistent_store.list_sessions()
        
        return list(self.sessions.keys())

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            True if deleted successfully, False otherwise.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
        
        if self.use_persistence and self.persistent_store:
            return self.persistent_store.delete_session(session_id)
        
        return True

    # MemoryObject-specific methods
    def store(self, memory_obj: MemoryObject) -> str:
        """Store a MemoryObject and persist it to disk if enabled.

        Args:
            memory_obj: MemoryObject instance.

        Returns:
            MemoryObject ID.
        """
        self.objects[memory_obj.id] = memory_obj
        if self.use_persistence:
            filepath = self.objects_path / f"{memory_obj.id}.json"
            with open(filepath, "w") as f:
                json.dump(memory_obj.model_dump(), f, indent=2, default=str)
        return memory_obj.id

    def list_all(self) -> List[MemoryObject]:
        """List all MemoryObjects.

        Returns:
            List of MemoryObject instances.
        """
        return list(self.objects.values())

    def retrieve(self, memory_id: str) -> Optional[MemoryObject]:
        """Retrieve a MemoryObject by ID.

        Args:
            memory_id: MemoryObject identifier.

        Returns:
            MemoryObject instance if found, else None.
        """
        if memory_id in self.objects:
            return self.objects[memory_id]

        if self.use_persistence:
            filepath = self.objects_path / f"{memory_id}.json"
            if filepath.exists():
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        obj = MemoryObject(**data)
                        self.objects[memory_id] = obj
                        return obj
                except Exception:
                    pass
        return None

    def search_by_tag(self, tag: str) -> List[MemoryObject]:
        """Search MemoryObjects by tag.

        Args:
            tag: Tag to search for.

        Returns:
            List of matching MemoryObject instances.
        """
        return [obj for obj in self.objects.values() if tag in obj.tags]

    def search_by_type(self, object_type: str) -> List[MemoryObject]:
        """Search MemoryObjects by type.

        Args:
            object_type: Object type to search for.

        Returns:
            List of matching MemoryObject instances.
        """
        return [obj for obj in self.objects.values() if obj.object_type == object_type]

    def _load_all_objects(self) -> None:
        """Load all persisted memory objects from disk."""
        if not self.use_persistence or not self.objects_path.exists():
            return
        for filepath in self.objects_path.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    obj = MemoryObject(**data)
                    self.objects[obj.id] = obj
            except Exception as e:
                print(f"Error loading memory object from {filepath}: {e}")

    def export_state(self) -> Dict[str, Any]:
        """Export current memory state.

        Returns:
            A dictionary summary of all sessions and memory objects.
        """
        return {
            "sessions": [s.model_dump() for s in self.sessions.values()],
            "objects": [obj.model_dump() for obj in self.objects.values()]
        }
