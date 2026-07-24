"""Context tracking component for SAGE Continuity Intelligence."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from sage.acr.session.session_state import SessionStateManager


class ContextTransition(BaseModel):
    """Represents a shift in context, e.g. switching milestone, objective, or state."""

    from_state: str
    to_state: str
    reason: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContinuityContext(BaseModel):
    """Structured continuity information representing the active project context."""

    current_project_state: str = "active"
    active_milestone: Optional[str] = None
    unresolved_items: List[str] = Field(default_factory=list)
    recent_changes: List[str] = Field(default_factory=list)
    important_context_transitions: List[ContextTransition] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ContextTracker:
    """Manages context tracking, transition logging, and previous session queries."""

    def __init__(
        self,
        storage_path: str = "sage_data/context",
        session_manager: Optional[SessionStateManager] = None,
    ):
        """Initialize Context Tracker.

        Args:
            storage_path: Directory for context persistence.
            session_manager: Optional SessionStateManager instance for lineage queries.
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.session_manager = session_manager or SessionStateManager()
        self.context: Optional[ContinuityContext] = None
        self._load_context()

    def get_current_context(self) -> ContinuityContext:
        """Get the active context, initializing if None."""
        if self.context is None:
            self.context = ContinuityContext()
        return self.context

    def _get_context_file_path(self) -> Path:
        """Get path to the context file."""
        return self.storage_path / "continuity_context.json"

    def _load_context(self) -> None:
        """Load context from disk if present."""
        filepath = self._get_context_file_path()
        if filepath.exists():
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    self.context = ContinuityContext(**data)
            except Exception:
                self.context = ContinuityContext()
        else:
            self.context = ContinuityContext()

    def save_context(self, context: Optional[ContinuityContext] = None) -> None:
        """Save context to disk."""
        if context is not None:
            self.context = context
        current = self.get_current_context()
        filepath = self._get_context_file_path()
        with open(filepath, "w") as f:
            json.dump(current.model_dump(), f, indent=2, default=str)

    def record_transition(
        self, from_state: str, to_state: str, reason: Optional[str] = None
    ) -> None:
        """Record an important context transition."""
        transition = ContextTransition(
            from_state=from_state,
            to_state=to_state,
            reason=reason,
        )
        ctx = self.get_current_context()
        ctx.important_context_transitions.append(transition)
        self.save_context()

    def set_milestone(self, milestone: str, reason: Optional[str] = None) -> None:
        """Update active milestone with a transition log."""
        ctx = self.get_current_context()
        old_milestone = ctx.active_milestone or "None"
        ctx.active_milestone = milestone
        self.record_transition(f"milestone:{old_milestone}", f"milestone:{milestone}", reason)

    def add_unresolved_item(self, item: str) -> None:
        """Record an unresolved/pending item in the context."""
        ctx = self.get_current_context()
        if item not in ctx.unresolved_items:
            ctx.unresolved_items.append(item)
            self.save_context()

    def resolve_item(self, item: str) -> None:
        """Mark an item resolved in the context."""
        ctx = self.get_current_context()
        if item in ctx.unresolved_items:
            ctx.unresolved_items.remove(item)
            ctx.recent_changes.append(f"Resolved: {item}")
            self.save_context()

    def add_recent_change(self, change: str) -> None:
        """Add a log entry of recent changes."""
        ctx = self.get_current_context()
        ctx.recent_changes.append(change)
        self.save_context()

    def get_previous_context(self, lineage: List[str]) -> Optional[Dict[str, Any]]:
        """Understand "What was happening before this session?" by traversing session history.

        Args:
            lineage: Order list of historical session IDs.

        Returns:
            A dictionary containing historical objectives, completed actions, and pending items.
        """
        if not lineage:
            return None

        # The parent session is typically the last or second-to-last item depending on if current is in lineage.
        parent_id = lineage[-1]
        parent_state = self.session_manager.retrieve_session(parent_id)
        if not parent_state:
            # Try earlier sessions if parent not found
            for prev_id in reversed(lineage[:-1]):
                parent_state = self.session_manager.retrieve_session(prev_id)
                if parent_state:
                    break

        if not parent_state:
            return None

        # Build structured previous context summary
        return {
            "session_id": parent_state.session_id,
            "timestamp": parent_state.timestamp.isoformat(),
            "last_objectives": parent_state.active_objectives.copy(),
            "last_completed_actions": parent_state.completed_actions.copy(),
            "last_pending_actions": parent_state.pending_actions.copy(),
            "last_important_decisions": parent_state.important_decisions.copy(),
            "last_archive_references": parent_state.related_archive_references.copy(),
        }
