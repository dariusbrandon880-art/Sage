"""State Transition Protocol (STP) tracking and rollback engine.

Transactionally manages SAGE state mutations (S0 -> Delta -> Evidence -> Validation -> S1)
and automatically executes rollbacks on validation or execution failures.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class STPState(str, Enum):
    """Stages of the State Transition Protocol."""

    S0 = "S0"  # Stable initial state
    DELTA = "DELTA"  # Proposed change stage
    EVIDENCE = "EVIDENCE"  # Evidence attachment stage
    VALIDATION = "VALIDATION"  # Validation review stage
    S1 = "S1"  # Committed stable state


class StateTransition(BaseModel):
    """Represents a transactional state transition."""

    transition_id: str = Field(default_factory=lambda: f"stp_{uuid.uuid4().hex[:8]}")
    stage: STPState = STPState.S0
    from_state: dict[str, Any] = Field(default_factory=dict)
    to_state: dict[str, Any] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = Field(default_factory=dict)


class StateTransitionEngine:
    """STP Rollback & Tracking Engine."""

    def __init__(self, runtime: Any):
        """Initialize STP engine.

        Args:
            runtime: SAGERuntime process host.
        """
        self.runtime = runtime
        self.transitions: dict[str, StateTransition] = {}

    def begin_mutation(self, description: str, metadata: dict[str, Any] | None = None) -> str:
        """Start a new state mutation transaction, capturing the S0 stable state."""
        # Capture current S0 runtime state
        s0_state = {
            "current_objective": self.runtime.current_state.current_objective,
            "active_task": self.runtime.current_state.active_task,
            "blockers": list(self.runtime.current_state.blockers),
            "dependencies": list(self.runtime.current_state.dependencies),
        }

        transition = StateTransition(
            stage=STPState.DELTA,
            from_state=s0_state,
            metadata={"description": description, **(metadata or {})},
        )
        self.transitions[transition.transition_id] = transition
        return transition.transition_id

    def register_evidence(self, transition_id: str, evidence_id: str) -> None:
        """Link an evidence memory/decision to the active mutation transaction."""
        transition = self.transitions.get(transition_id)
        if not transition:
            raise ValueError(f"STP Transition '{transition_id}' not found.")

        transition.stage = STPState.EVIDENCE
        if evidence_id not in transition.evidence_ids:
            transition.evidence_ids.append(evidence_id)

    def validate_transition(self, transition_id: str) -> bool:
        """Validate the active mutation transition against SAGE quality standards."""
        transition = self.transitions.get(transition_id)
        if not transition:
            raise ValueError(f"STP Transition '{transition_id}' not found.")

        transition.stage = STPState.VALIDATION

        # Run validation over all linked evidence items
        for ev_id in transition.evidence_ids:
            is_valid, _ = self.runtime.validation.validate_memory(ev_id)
            if not is_valid:
                # Execution failure: Trigger automatic rollback
                self.execute_rollback(transition_id)
                return False

        return True

    def commit_transition(self, transition_id: str) -> None:
        """Commit the mutation transaction to S1 committed state."""
        transition = self.transitions.get(transition_id)
        if not transition:
            raise ValueError(f"STP Transition '{transition_id}' not found.")

        transition.stage = STPState.S1
        # Capture final committed S1 state
        transition.to_state = {
            "current_objective": self.runtime.current_state.current_objective,
            "active_task": self.runtime.current_state.active_task,
            "blockers": list(self.runtime.current_state.blockers),
            "dependencies": list(self.runtime.current_state.dependencies),
        }

        # Log to telemetry
        from sage.runtime.metrics import get_metrics_collector

        metrics = get_metrics_collector()
        metrics.increment("stp.commits.total")
        metrics.record_event(
            "stp_transition_committed",
            {
                "transition_id": transition_id,
                "description": transition.metadata.get("description"),
            },
        )

    def execute_rollback(self, transition_id: str) -> None:
        """Execute a clean rollback to restore S0 state, removing temporary evidence artifacts."""
        transition = self.transitions.get(transition_id)
        if not transition:
            raise ValueError(f"STP Transition '{transition_id}' not found.")

        # 1. Restore original S0 runtime state
        s0 = transition.from_state
        self.runtime.current_state.current_objective = s0.get("current_objective")
        self.runtime.current_state.active_task = s0.get("active_task")
        self.runtime.current_state.blockers = list(s0.get("blockers", []))
        self.runtime.current_state.dependencies = list(s0.get("dependencies", []))
        self.runtime._save_state()

        # 2. Delete temporary/un-validated evidence items ingested during this transaction
        for ev_id in transition.evidence_ids:
            # Check if it exists in memory store
            obj = self.runtime.memory.retrieve(ev_id)
            if (
                obj
                and hasattr(self.runtime.memory, "objects")
                and ev_id in self.runtime.memory.objects
            ):
                del self.runtime.memory.objects[ev_id]
                # Delete file if present on disk
                filepath = Path(self.runtime.memory.storage_path) / f"{ev_id}.json"
                if filepath.exists():
                    try:
                        filepath.unlink()
                    except OSError:
                        pass

        transition.stage = STPState.S0  # Reverted back to initial state S0

        # Log rollback to metrics
        from sage.runtime.metrics import get_metrics_collector

        metrics = get_metrics_collector()
        metrics.increment("stp.rollbacks.total")
        metrics.record_event("stp_transition_rolled_back", {"transition_id": transition_id})
