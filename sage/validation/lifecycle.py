"""Evidence and Knowledge Lifecycle Management for SAGE."""

from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LifecycleState(str, Enum):
    """Lifecycle states for evidence and knowledge assets."""

    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    VALIDATED = "validated"
    PROMOTED = "promoted"
    ARCHIVED = "archived"


class LifecycleHistoryEntry(BaseModel):
    """Entry logging a transition in the lifecycle of an asset."""

    from_state: Optional[LifecycleState] = None
    to_state: LifecycleState
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str = "system"
    reason: Optional[str] = None


class LifecycleManager(BaseModel):
    """Tracks and validates lifecycle transitions of SAGE knowledge assets."""

    item_id: str
    current_state: LifecycleState = LifecycleState.PROPOSED
    history: List[LifecycleHistoryEntry] = Field(default_factory=list)

    def transition_to(
        self,
        new_state: LifecycleState,
        actor: str = "system",
        reason: Optional[str] = None,
    ) -> bool:
        """Attempt to transition the asset to a new lifecycle state.

        Returns:
            True if transition succeeded, False otherwise.
        """
        # Validate state machine transition boundaries
        allowed = False

        if self.current_state == LifecycleState.PROPOSED:
            # Proposed can move to Under Review or directly to Validated
            allowed = new_state in (LifecycleState.UNDER_REVIEW, LifecycleState.VALIDATED)
        elif self.current_state == LifecycleState.UNDER_REVIEW:
            # Under Review can move back to Proposed (if rejected) or Validated
            allowed = new_state in (LifecycleState.PROPOSED, LifecycleState.VALIDATED)
        elif self.current_state == LifecycleState.VALIDATED:
            # Validated can move to Promoted
            allowed = new_state == LifecycleState.PROMOTED
        elif self.current_state == LifecycleState.PROMOTED:
            # Promoted can move to Archived
            allowed = new_state == LifecycleState.ARCHIVED
        elif self.current_state == LifecycleState.ARCHIVED:
            # Archived is terminal (cannot transition out of Archived)
            allowed = False

        if not allowed:
            return False

        # Apply transition
        entry = LifecycleHistoryEntry(
            from_state=self.current_state,
            to_state=new_state,
            actor=actor,
            reason=reason,
        )
        self.history.append(entry)
        self.current_state = new_state
        return True
