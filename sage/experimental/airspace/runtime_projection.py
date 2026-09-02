"""Read-only projection from canonical SageRuntime state into Airspace immersion."""

from __future__ import annotations

import hashlib

from sage.experimental.airspace.models import AirspaceState, Mission, StationID


def _derived_mission_id(objective: str) -> str:
    """Create a stable projection identifier without creating canonical state."""
    digest = hashlib.sha256(objective.encode("utf-8")).hexdigest()[:16]
    return f"runtime:{digest}"


def project_runtime_state(runtime) -> AirspaceState:
    """Project canonical runtime state into the existing Airspace presentation model.

    This function is intentionally read-only. It does not mutate runtime state,
    create sorties, authorize execution, or introduce an alternate source of truth.
    """
    current_state = runtime.current_state
    objective = getattr(current_state, "current_objective", None)
    task = getattr(current_state, "active_task", None)
    blockers = list(getattr(current_state, "blockers", []) or [])
    context = getattr(runtime, "context", None)
    session_id = getattr(context, "session_id", None) or "unbound"

    mission = None
    if objective:
        mission = Mission(
            mission_id=_derived_mission_id(objective),
            mission_name="Canonical Runtime Objective",
            theater="SAGE Runtime",
            priority="P0",
            objective=objective,
            constraints=[f"BLOCKER: {blocker}" for blocker in blockers],
            status="ACTIVE",
            current_frontier=task or "UNSPECIFIED",
        )

    return AirspaceState(
        session_id=session_id,
        mode="OPERATIONAL",
        stations={StationID.MISSION_CONTROL: {"agent_name": "ChatGPT"}},
        active_mission=mission,
        current_frontiers=[task] if task else [],
        recent_evidence=[],
        next_clearance="UNSPECIFIED",
        active_sorties=[],
    )
