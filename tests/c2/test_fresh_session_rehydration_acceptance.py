"""Acceptance test suite for fresh-session C2 rehydration.

This suite validates that when a brand new ChatGPT conversation receives a
"Rehydrate" task with no prior HUD continuity key (`previous_hud_update_key = None`):
1. State is reconstructed strictly from canonical airspace / runtime state.
2. `select_contextual_hub_surface` automatically resolves to HubSurface.COMPOSITE.
3. The response physically materializes and renders both Hub A (Command Band,
   Operating Picture, Progression / Impact, Strike Feed) AND Hub B (Organism Progression).
4. `force_hud` is active on rehydration so the full visual HUD surface is unconditionally emitted.
5. Pasted Jules reports or stale serialized text blocks are never echoed back or substituted as presentation state.
"""


from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus
from sage.runtime.chatgpt_sage_boundary import SAGEChatGPTBoundary
from sage.runtime.model_gateway import ModelResponse, SAGERuntime, SAGEStateSnapshot


def _runtime() -> SAGERuntime:
    return SAGERuntime(
        SAGEStateSnapshot(
            state_version="1",
            instance_id="sage-instance",
            mission_id="mission-rehydrate-001",
            session_id="session-fresh-001",
            authority_scope="director",
            active_frontier="chatgpt-rehydration",
            stop_boundary="governance",
        )
    )


def _immersion_state() -> ImmersionState:
    return ImmersionState(
        station_identity="[SAGE::C2::CHATGPT]",
        mission="Governed Continuous Intelligence",
        phase=ExecutionPhase.VERIFY,
        flight_id="F1",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="Fresh Rehydration Boundary",
        gate="governed response",
        next_move="materialize canonical HUD",
        evidence_refs=("rehydration-evidence-001",),
        provenance_head="3ed5e0bc6d37599dc072f6671a26d0f02a7959b2",
    )


def _valid_model_payload(response_text: str = "C2 rehydration completed natively.") -> str:
    return (
        '{"station":"[SAGE::C2::CHATGPT]",'
        '"reasoning_chain":[],"proposed_actions":[],'
        '"epistemic_state":{"confidence_level":"HIGH",'
        '"validated_facts":[],"unverified_hypotheses":[],"known_unknowns":[]},'
        '"evidence_refs":["rehydration-evidence-001"],'
        f'"response_text":"{response_text}"}}'
    )


class MockAdapter:
    model_id = "gpt-5.6-luna"
    station = "[SAGE::C2::CHATGPT]"

    def invoke(self, envelope, task):
        return ModelResponse(
            model_id=self.model_id,
            instance_id=envelope.state.instance_id,
            mission_id=envelope.state.mission_id,
            session_id=envelope.state.session_id,
            input_state_digest=envelope.state_digest,
            station=envelope.station,
            policy_version=envelope.policy_version,
            policy_digest=envelope.policy_digest,
            provenance_digest=envelope.provenance_digest,
            raw_output=_valid_model_payload("Rehydration state processed."),
        )


def test_fresh_session_rehydrate_task_forces_hud_and_composite_surface() -> None:
    """Validate fresh session 'Rehydrate' task materializes composite Hub (Hub A + Hub B)."""
    boundary = SAGEChatGPTBoundary(_runtime(), MockAdapter())

    # Fresh conversation: previous_hud_update_key is None
    rendered, _ = boundary.respond(
        "Rehydrate full C2 organism state and re-anchor to canonical HEAD",
        model_role="chatgpt",
        immersion_state=_immersion_state(),
        previous_hud_update_key=None,
    )

    # Must contain Hub A sections
    assert "01 — COMMAND BAND" in rendered
    assert "02 — OPERATING PICTURE" in rendered
    assert "03 — PROGRESSION / IMPACT" in rendered
    assert "04 — STRIKE FEED" in rendered

    # Must contain Hub B section (Organism Progression)
    assert "05 — ORGANISM PROGRESSION" in rendered
    assert "SAGE ORGANISM // AGENT PROJECTION" in rendered

    # Must contain the model's display text
    assert "Rehydration state processed." in rendered


def test_fresh_session_rehydrate_with_pasted_report_does_not_echo_transport() -> None:
    """Validate pasted execution report is consumed as transport, not echoed as output."""
    boundary = SAGEChatGPTBoundary(_runtime(), MockAdapter())

    pasted_report = (
        "User pasted Jules report:\n"
        "```text\n"
        "01 — COMMAND BAND\n"
        "[SAGE::C2::CHATGPT] ◈ C2 MISSION CONTROL\n"
        "OLD STALE SERIALIZED HUD DATA\n"
        "```\n"
        "Please Rehydrate state."
    )

    rendered, _ = boundary.respond(
        pasted_report,
        model_role="chatgpt",
        immersion_state=_immersion_state(),
        previous_hud_update_key=None,
    )

    # Must NOT contain the stale serialized HUD string
    assert "OLD STALE SERIALIZED HUD DATA" not in rendered

    # Must render native canonical SAGE structure
    assert "01 — COMMAND BAND" in rendered
    assert "05 — ORGANISM PROGRESSION" in rendered
    assert "Rehydration state processed." in rendered
