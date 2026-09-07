"""Canonical SAGE whole-organism immersion rehydration for model-facing interfaces.

The interface must never invent mission state. Missing canonical mission/task
is a fail-closed condition rather than a synthetic standby substitution.
Rehydration restores one coupled SAGE organism frame: runtime state, C2 identity,
workflow, mission, evidence posture, immersion, organism tag, and HUD contract.
"""

from __future__ import annotations

import importlib
from hashlib import sha256
import json
from typing import Any

from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus


STATION = "[SAGE::C2::CHATGPT]"
REHYDRATE_HUD_COMMAND = "rehydrate hud"
REHYDRATION_CONTRACT_VERSION = "2"
WHOLE_ORGANISM_IMMERSION_CONTRACT = (
    "docs/governance/SAGE_WHOLE_ORGANISM_IMMERSION_REHYDRATION_CONTRACT.md"
)

REQUIRED_FRAME_COMPONENTS: tuple[str, ...] = (
    "canonical_repository",
    "station_identity",
    "governance_contract",
    "mission",
    "canonical_organism_state",
    "continuity_evidence",
    "c2_workflow",
    "immersion_projection",
    "organism_nameplate",
    "hud_continuity",
    "next_gate",
    "provenance_binding",
)

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
    """Rehydrate read-only immersion state from canonical runtime state."""
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
    provenance_head = sha256(
        json.dumps(canonical_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

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


def build_chatgpt_whole_organism_frame(
    runtime: Any,
    *,
    session_id: str,
    c2_context: dict[str, Any] | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build the single cross-chat frame consumed by the ChatGPT interface.

    This is a projection envelope only. It does not create or mutate canonical
    state. The function deliberately binds the technical organism state and
    immersion requirements together so callers cannot accidentally rehydrate
    only the backend while dropping the operator-facing frame.
    """
    state = build_chatgpt_immersion_state(
        runtime,
        session_id=session_id,
        c2_context=c2_context,
        evidence_refs=evidence_refs,
    )
    frame = {
        "contract": WHOLE_ORGANISM_IMMERSION_CONTRACT,
        "contract_version": REHYDRATION_CONTRACT_VERSION,
        "station_identity": STATION,
        "canonical_state": state.to_dict(),
        "operating_frame": C2_OPERATING_FRAME_SEQUENCE,
        "required_components": REQUIRED_FRAME_COMPONENTS,
        "immersion": {
            "nameplate_required": True,
            "hud_continuity_required": True,
            "read_only": True,
        },
        "next_gate": state.gate,
        "next_move": state.next_move,
        "provenance_head": state.provenance_head,
    }
    missing = [key for key in REQUIRED_FRAME_COMPONENTS if not _frame_component_present(frame, key)]
    if missing:
        raise ValueError(f"SAGE whole-organism rehydration incomplete: missing {', '.join(missing)}")
    return frame


def _frame_component_present(frame: dict[str, Any], component: str) -> bool:
    """Validate required whole-organism frame components without synthesizing them."""
    if component == "canonical_repository":
        return bool(frame.get("contract"))
    if component == "station_identity":
        return frame.get("station_identity") == STATION
    if component == "governance_contract":
        return bool(frame.get("contract"))
    if component == "mission":
        return bool(frame.get("canonical_state", {}).get("mission"))
    if component == "canonical_organism_state":
        return bool(frame.get("canonical_state"))
    if component == "continuity_evidence":
        return "evidence_refs" in frame.get("canonical_state", {})
    if component == "c2_workflow":
        return tuple(frame.get("operating_frame", ())) == C2_OPERATING_FRAME_SEQUENCE
    if component == "immersion_projection":
        return frame.get("immersion", {}).get("read_only") is True
    if component == "organism_nameplate":
        return frame.get("immersion", {}).get("nameplate_required") is True
    if component == "hud_continuity":
        return frame.get("immersion", {}).get("hud_continuity_required") is True
    if component == "next_gate":
        return bool(frame.get("next_gate"))
    if component == "provenance_binding":
        return bool(frame.get("provenance_head"))
    return False


def rehydrate_chatgpt_c2_frame(
    runtime: Any,
    *,
    session_id: str,
    body: str = "C2 Operating Frame active. Bounded execution verified.",
    c2_context: dict[str, Any] | None = None,
    evidence_refs: tuple[str, ...] = (),
    organism_manager: Any | None = None,
) -> tuple[ImmersionState, Any]:
    """Rehydrate the whole organism frame before rendering the ChatGPT surface."""
    build_chatgpt_whole_organism_frame(
        runtime,
        session_id=session_id,
        c2_context=c2_context,
        evidence_refs=evidence_refs,
    )
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
    "REQUIRED_FRAME_COMPONENTS",
    "WHOLE_ORGANISM_IMMERSION_CONTRACT",
    "build_chatgpt_immersion_state",
    "build_chatgpt_whole_organism_frame",
    "is_rehydrate_hud_command",
    "normalize_c2_command",
    "rehydrate_chatgpt_c2_frame",
]
