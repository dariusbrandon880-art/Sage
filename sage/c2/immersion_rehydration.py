"""Canonical SAGE immersion rehydration for model-facing interfaces.

The interface must never invent mission state. Missing canonical mission/task
is a fail-closed condition rather than a synthetic standby substitution.
Rehydrates full game immersion, canonical organism state, and C2 operating frame.
"""

from __future__ import annotations

import importlib
from hashlib import sha256
import json
from typing import Any

from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus


STATION = "[SAGE::C2::CHATGPT]"
REHYDRATE_HUD_COMMAND = "rehydrate hud"
REHYDRATION_CONTRACT_VERSION = "1"

C2_OPERATING_FRAME_SEQUENCE: tuple[str, ...] = (
    "LIVE REPO",
    "FULL WORKFLOW RECON",
    "CANONICAL ARCHITECTURE",
    "ACTIVE FRONTIER",
    "ENGINEER",
    "TEST",
    "EVIDENCE",
    "VERIFY",
    "PROMOTE",
)


def normalize_c2_command(command: str) -> str:
    """Normalize a model-facing C2 command without changing its semantics."""
    if not isinstance(command, str):
        return ""
    return " ".join(command.strip().casefold().split())


def is_rehydrate_hud_command(command: str) -> bool:
    """Return whether input is the canonical REHYDRATE HUD command."""
    return normalize_c2_command(command) == REHYDRATE_HUD_COMMAND


def _load_airspace_manager() -> Any | None:
    try:
        mod = importlib.import_module("sage.experimental.airspace.manager")
        return mod.AirspaceManager()
    except Exception:
        return None


def build_chatgpt_immersion_state(
    runtime: Any,
    *,
    session_id: str,
    c2_context: dict[str, Any] | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> ImmersionState:
    """Rehydrate a read-only immersion state from canonical runtime state."""
    if not session_id or not session_id.strip():
        raise ValueError("SAGE immersion rehydration requires a session_id")

    current_state = getattr(runtime, "current_state", None)
    if current_state is None:
        raise ValueError("SAGE immersion rehydration requires canonical runtime state")

    context = dict(c2_context or {})
    raw_mission = context.get("active_objective") or getattr(current_state, "current_objective", None)
    raw_task = context.get("active_task") or getattr(current_state, "active_task", None)
    if not raw_mission or not str(raw_mission).strip():
        raise ValueError("SAGE immersion rehydration requires canonical active objective")
    if not raw_task or not str(raw_task).strip():
        raise ValueError("SAGE immersion rehydration requires canonical active task")
    mission = str(raw_mission).strip()
    task = str(raw_task).strip()

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
        "contract_version": REHYDRATION_CONTRACT_VERSION,
        "command": REHYDRATE_HUD_COMMAND,
        "session_id": session_id,
        "objective": mission,
        "task": task,
        "operating_frame": list(C2_OPERATING_FRAME_SEQUENCE),
        "blockers": list(getattr(current_state, "blockers", []) or []),
        "dependencies": list(getattr(current_state, "dependencies", []) or []),
    }
    provenance_head = sha256(json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    frontier = context.get("active_frontier") or context.get("frontier") or "c2-runtime-boundary"
    gate = context.get("gate") or "GOVERNED_EXECUTION"
    trust_status = TrustStatus.VERIFIED if c2_status.get("rehydrated", True) else TrustStatus.HOLD

    state = ImmersionState(
        station_identity=STATION,
        mission=mission,
        phase=ExecutionPhase.EXECUTE,
        flight_id=f"C2:{session_id}",
        flight_status=FlightStatus.ACTIVE,
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


def rehydrate_chatgpt_c2_frame(
    runtime: Any,
    *,
    session_id: str,
    body: str = "C2 Operating Frame active. Bounded execution verified.",
    c2_context: dict[str, Any] | None = None,
    evidence_refs: tuple[str, ...] = (),
    organism_manager: Any | None = None,
) -> tuple[ImmersionState, Any]:
    """Rehydrate complete C2 frame with full game immersion and canonical organism state."""
    immersion_state = build_chatgpt_immersion_state(
        runtime,
        session_id=session_id,
        c2_context=c2_context,
        evidence_refs=evidence_refs,
    )

    mgr = organism_manager or _load_airspace_manager()

    chatgpt_runtime_mod = importlib.import_module("sage.c2.chatgpt_runtime")
    response = chatgpt_runtime_mod.build_chatgpt_c2_response(
        immersion_state,
        body=body,
        organism_manager=mgr,
    )
    return immersion_state, response


__all__ = [
    "C2_OPERATING_FRAME_SEQUENCE",
    "REHYDRATE_HUD_COMMAND",
    "REHYDRATION_CONTRACT_VERSION",
    "build_chatgpt_immersion_state",
    "is_rehydrate_hud_command",
    "normalize_c2_command",
    "rehydrate_chatgpt_c2_frame",
]
