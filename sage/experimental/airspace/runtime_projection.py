"""Read-only projection from canonical SAGE runtime state into Airspace.

Airspace is an observability/immersion surface. This module derives its view
from the canonical runtime and never writes runtime state, creates missions,
or authorizes execution.
"""

from __future__ import annotations

import hashlib
from typing import Any

from sage.experimental.airspace.models import AirspaceState, Mission


def _derived_mission_id(objective: str) -> str:
    """Create a stable projection identifier from the canonical objective."""
    digest = hashlib.sha256(objective.encode("utf-8")).hexdigest()[:12]
    return f"runtime-objective-{digest}"


def project_runtime_state(runtime: Any) -> AirspaceState:
    """Project canonical ``SageRuntime.current_state`` into Airspace.

    Only values that already exist in canonical runtime state are projected.
    Missing operational concepts remain explicitly unbound instead of being
    synthesized by the game/immersion layer.
    """
    canonical = runtime.current_state
    objective = getattr(canonical, "current_objective", None)
    task = getattr(canonical, "active_task", None)
    blockers = list(getattr(canonical, "blockers", []) or [])

    session_id = "unbound"
    context = getattr(runtime, "context", None)
    if context is not None and getattr(context, "session_id", None):
        session_id = context.session_id

    state = AirspaceState(
        session_id=session_id,
        mode="OPERATIONAL",
        current_frontiers=[task] if task else [],
        recent_evidence=[],
        next_clearance="UNSPECIFIED",
    )

    if objective:
        state.active_mission = Mission(
            mission_id=_derived_mission_id(objective),
            mission_name="Canonical Runtime Objective",
            theater="SAGE Runtime",
            priority="P0",
            objective=objective,
            constraints=[f"BLOCKER: {blocker}" for blocker in blockers],
            status="ACTIVE",
            current_frontier=task or "UNSPECIFIED",
        )

    return state


__all__ = ["project_runtime_state"]
