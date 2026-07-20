"""ACR Continuity Bridge for maintaining state across sessions."""

from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from pathlib import Path
from pydantic import BaseModel, Field


class ContinuityState(BaseModel):
    """Model for persistent continuity state."""
    
    id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    data: Dict[str, Any] = Field(default_factory=dict)
    session_lineage: List[str] = Field(default_factory=list)


import os

class ACRBridge:
    """Bridge for Autonomous Continuity Runtime - manages cross-session state with persistence."""

    def __init__(self, persistence_path: Optional[str] = None, use_persistence: bool = True):
        """Initialize ACR bridge.
        
        Args:
            persistence_path: Path for storing continuity state. Defaults to .sage/continuity
            use_persistence: Whether to use persistent storage.
        """
        self.continuity_state: Dict[str, Any] = {}
        self.session_lineage: List[str] = []
        self.use_persistence = use_persistence

        # Prevent test state leakage under pytest
        if self.use_persistence and "PYTEST_CURRENT_TEST" in os.environ and not persistence_path:
            import tempfile
            self.persistence_path = Path(tempfile.mkdtemp(prefix="sage_test_continuity_"))
        else:
            self.persistence_path = Path(persistence_path or ".sage/continuity")
        
        if self.use_persistence:
            self.persistence_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing state if available
        self._load_persisted_state()

    def _get_state_file_path(self) -> Path:
        """Get the path for the continuity state file."""
        return self.persistence_path / "continuity_state.json"

    def _load_persisted_state(self) -> None:
        """Load continuity state from persistent storage."""
        if not self.use_persistence:
            return
        
        state_file = self._get_state_file_path()
        if not state_file.exists():
            return
        
        try:
            with open(state_file, "r") as f:
                data = json.load(f)
            
            self.continuity_state = data.get("data", {})
            self.session_lineage = data.get("session_lineage", [])
        except (json.JSONDecodeError, IOError):
            pass

    def _save_persisted_state(self) -> None:
        """Persist continuity state to storage."""
        if not self.use_persistence:
            return
        
        state_file = self._get_state_file_path()
        
        data = {
            "id": "global_continuity",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data": self.continuity_state,
            "session_lineage": self.session_lineage,
        }
        
        try:
            with open(state_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save continuity state for next session.
        
        Args:
            state: State dictionary to persist.
        """
        self.continuity_state = state.copy()
        self._save_persisted_state()

    def load_state(self) -> Dict[str, Any]:
        """Load previously saved continuity state.
        
        Returns:
            Continuity state dictionary.
        """
        return self.continuity_state.copy()

    def add_session_link(self, session_id: str) -> None:
        """Add session to continuity lineage.
        
        Args:
            session_id: Session identifier to link.
        """
        self.session_lineage.append(session_id)
        self._save_persisted_state()

    def get_lineage(self) -> List[str]:
        """Get session lineage chain.
        
        Returns:
            List of session IDs in order.
        """
        return self.session_lineage.copy()

    def get_parent_session(self) -> Optional[str]:
        """Get the ID of the parent session.
        
        Returns:
            Parent session ID or None if no lineage.
        """
        return self.session_lineage[-1] if self.session_lineage else None

    def get_session_depth(self) -> int:
        """Get the depth of the session lineage.
        
        Returns:
            Number of sessions in lineage.
        """
        return len(self.session_lineage)

    def update_state_value(self, key: str, value: Any) -> None:
        """Update a single value in continuity state.
        
        Args:
            key: State key.
            value: New value.
        """
        self.continuity_state[key] = value
        self._save_persisted_state()

    def get_state_value(self, key: str, default: Any = None) -> Any:
        """Retrieve a single value from continuity state.
        
        Args:
            key: State key.
            default: Default value if key not found.
            
        Returns:
            State value or default.
        """
        return self.continuity_state.get(key, default)

    def clear_state(self) -> None:
        """Clear all continuity state."""
        self.continuity_state.clear()
        self.session_lineage.clear()
        self._save_persisted_state()

    def export_lineage_graph(self) -> Dict[str, Any]:
        """Export the session lineage as a graph structure.
        
        Returns:
            Lineage graph with metadata.
        """
        return {
            "depth": self.get_session_depth(),
            "lineage": self.get_lineage(),
            "parent": self.get_parent_session(),
            "root": self.session_lineage[0] if self.session_lineage else None,
            "continuity_state_keys": list(self.continuity_state.keys()),
        }
