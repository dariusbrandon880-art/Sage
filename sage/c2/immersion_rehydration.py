"""Canonical SAGE immersion rehydration for model-facing interfaces.

The interface must never invent mission state. When no mission/task is active,
the canonical runtime projects an explicit standby state rather than falling
back to a synthetic flight or conversation-local state.
"""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any

from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus


STATION = "[SAGE::C2::CHATGPT]"


def build_chatgpt_immersion_state(
    runtime: Any,
    *,
    session_id: str,
    c2_context: dict[str, Any] | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> ImmersionState:
    """Rehydrate a read-only immersion state from canonical runtime state.

    Missing mission/task is represented as canonical standby state. No model
    output, prompt text, or legacy hard-coded flight is allowed to fill the
    gap.
    """
    if not session_id or not session_id.strip():
        raise ValueError("SAGE immersion rehydration requires a session_id")

    current_state = getattr(runtime, "current_state", None)
    if current_state is None:
        raise ValueError("SAGE immersion rehydration requires canonical runtime state")

    context = dict(c2_context or {})
    raw_mission = context.get("active_objective") or getattr(current_state, "current_objective", None)
    raw_task = context.get("active_task") or getattr(current_state, "active_task", None)
    has_active_mission = bool(raw_mission and str(raw_mission).strip() and raw_task and str(raw_task).strip())
    mission = str(raw_mission).strip() if raw_mission and str(raw_mission).strip() else "SAGE Runtime Standby"
    task = str(raw_task).strip() if raw_task and str(raw_task).strip() else "Awaiting canonical mission assignment"

    status = {}
    if hasattr(runtime, "get_status") and callable(runtime.get_status):
        try:
            status = dict(runtime.get_status() or {})
        except Exception:
            status = {}

    c2_status = status.get("c2_status") if isinstance(status.get("c2_status"), dict) else {}
    if c2_status and c2_status.get("rehydrated") is False:
        raise ValueError("SAGE immersion rehydration blocked: C2 runtime is not rehydrated")

    canonical_payload = {
        "session_id": session_id,
        "objective": mission,
        "task": task,
        "blockers": list(getattr(current_state, "blockers", []) or []),
        "dependencies": list(getattr(current_state, "dependencies", []) or []),
    }
    provenance_head = sha256(json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    frontier = context.get("active_frontier") or context.get("frontier") or "c2-runtime-boundary"
    gate = context.get("gate") or "GOVERNED_EXECUTION"
    flight_status = FlightStatus.ACTIVE if has_active_mission else FlightStatus.STANDBY
    trust_status = TrustStatus.VERIFIED if c2_status.get("rehydrated", True) else TrustStatus.HOLD

    state = ImmersionState(
        station_identity=STATION,
        mission=mission,
        phase=ExecutionPhase.EXECUTE,
        flight_id=f"C2:{session_id}",
        flight_status=flight_status,
        trust_status=trust_status,
        frontier=str(frontier),
        gate=str(gate),
        next_move=task,
        evidence_refs=tuple(evidence_refs),
        provenance_head=provenance_head,
    )
    if not state.validate():
        raise ValueError("SAGE immersion rehydration produced invalid canonical state")
    return state
