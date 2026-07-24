"""Session state model and persistence manager for SAGE Continuity Intelligence."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SessionState(BaseModel):
    """Model representing structured SAGE session state."""

    session_id: str = Field(default_factory=lambda: f"session_{uuid.uuid4().hex[:8]}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_objectives: list[str] = Field(default_factory=list)
    completed_actions: list[str] = Field(default_factory=list)
    pending_actions: list[str] = Field(default_factory=list)
    important_decisions: list[str] = Field(default_factory=list)
    related_archive_references: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_objective(self, objective: str) -> None:
        """Add an active objective to the session."""
        if objective not in self.active_objectives:
            self.active_objectives.append(objective)

    def add_completed_action(self, action: str) -> None:
        """Add a completed action and remove from pending if present."""
        if action not in self.completed_actions:
            self.completed_actions.append(action)
        if action in self.pending_actions:
            self.pending_actions.remove(action)

    def add_pending_action(self, action: str) -> None:
        """Add a pending action."""
        if action not in self.pending_actions and action not in self.completed_actions:
            self.pending_actions.append(action)

    def add_decision(self, decision_id: str) -> None:
        """Link an important decision to this session."""
        if decision_id not in self.important_decisions:
            self.important_decisions.append(decision_id)

    def add_archive_reference(self, archive_id: str) -> None:
        """Link a related archive entry to this session."""
        if archive_id not in self.related_archive_references:
            self.related_archive_references.append(archive_id)


class SessionStateManager:
    """Manager to load, save, and list session states."""

    def __init__(self, storage_path: str = "sage_data/sessions"):
        """Initialize Session State Manager.

        Args:
            storage_path: Directory path for persisting session states.
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.sessions: dict[str, SessionState] = {}
        self._load_all_sessions()

    def create_session(
        self,
        session_id: str | None = None,
        active_objectives: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionState:
        """Create and record a new session state."""
        sess_id = session_id or f"session_{uuid.uuid4().hex[:8]}"
        state = SessionState(
            session_id=sess_id,
            active_objectives=active_objectives or [],
            metadata=metadata or {},
        )
        self.sessions[sess_id] = state
        self.save_session(state)
        return state

    def retrieve_session(self, session_id: str) -> SessionState | None:
        """Retrieve session state by ID."""
        if session_id in self.sessions:
            return self.sessions[session_id]

        filepath = self.storage_path / f"{session_id}.json"
        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    state = SessionState(**data)
                    self.sessions[session_id] = state
                    return state
            except Exception:
                pass
        return None

    def save_session(self, state: SessionState) -> None:
        """Persist a session state to disk."""
        self.sessions[state.session_id] = state
        filepath = self.storage_path / f"{state.session_id}.json"
        with open(filepath, "w") as f:
            json.dump(state.model_dump(), f, indent=2, default=str)

    def list_all(self) -> list[SessionState]:
        """List all managed session states."""
        return list(self.sessions.values())

    def _load_all_sessions(self) -> None:
        """Load all persisted session states from disk."""
        if not self.storage_path.exists():
            return
        for filepath in self.storage_path.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    state = SessionState(**data)
                    self.sessions[state.session_id] = state
            except Exception:
                pass
