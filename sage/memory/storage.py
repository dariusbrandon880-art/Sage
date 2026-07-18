"""Memory storage for session and context persistence."""

from typing import Optional, Dict, Any


class MemoryStore:
    """In-memory storage for session context and continuity state."""

    def __init__(self):
        """Initialize memory store."""
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.context: Dict[str, Any] = {}

    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create a new session in memory.
        
        Args:
            session_id: Unique session identifier.
            metadata: Optional session metadata.
        """
        self.sessions[session_id] = {"metadata": metadata or {}, "turns": []}

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            Session data or None if not found.
        """
        return self.sessions.get(session_id)

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
