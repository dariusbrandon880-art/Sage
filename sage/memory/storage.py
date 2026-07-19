"""Memory storage for session and context persistence."""

from typing import Optional, Dict, Any, List
from sage.memory.models import SessionMemory, RetrievalQuery
from sage.memory.persistence import PersistentMemoryStore


class MemoryStore:
    """Unified memory storage with both in-memory and persistent backends."""

    def __init__(self, persistent_path: Optional[str] = None, use_persistence: bool = True):
        """Initialize memory store.
        
        Args:
            persistent_path: Path for persistent storage. Defaults to .sage/memory
            use_persistence: Whether to use persistent storage backend.
        """
        self.sessions: Dict[str, SessionMemory] = {}
        self.context: Dict[str, Any] = {}
        self.use_persistence = use_persistence
        self.persistent_store = (
            PersistentMemoryStore(storage_path=persistent_path or ".sage/memory")
            if use_persistence
            else None
        )

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
