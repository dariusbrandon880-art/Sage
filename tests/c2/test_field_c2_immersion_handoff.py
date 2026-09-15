from __future__ import annotations

import pytest
from sage.c2.jules_report_ingestion import (
    JulesReport,
    compute_hud_projection_key,
    ingest_jules_report,
    rehydrate_c2_from_jules_report,
)
from sage.c2.response_envelope import build_response_envelope, c2_chatgpt_presentation
from sage.models import RuntimeState


SHA = "e8589d31629feb5ee6a5ea3f44f327f0b2c91885"
OTHER_SHA = "6a69a970d96582b7d0d53778cc1da3300eccdc84"


class FakeRuntime:
    def __init__(self, canonical_git_sha: str = SHA):
        self.payloads = []
        self.current_state = RuntimeState()
        self.canonical_git_sha = canonical_git_sha
        self.current_state.current_objective = "Canonical Active Objective"
        self.current_state.active_task = "Canonical Active Task"

    def ingest_session_payload(self, payload):
        self.payloads.append(payload)

    def get_status(self):
        return {"c2_status": {"rehydrated": True}}


def make_report_with_hud(**overrides):
    hud_proj = {
        "frontier": "field-c2-handoff",
        "gate": "GOVERNED_EXECUTION",
        "flight_id": "F1:jules_001",
        "phase": "EXECUTE",
        "trust_status": "VERIFIED",
    }
    calculated_key = compute_hud_projection_key(hud_proj)

    data = {
        "session_id": "session_jules_001",
        "report_id": "jules-report-001",
        "git_sha": SHA,
        "branch": "c2/jules-report-ingestion-contract",
        "status": "VERIFIED",
        "objective": "Make the Field-C2 HUD handoff real",
        "summary": "Completed Field-C2 to Tower-C2 structured handoff contract.",
        "evidence": ["pytest:tests/c2/test_field_c2_immersion_handoff.py"],
        "state_deltas": {"frontier": "field-c2-handoff"},
        "pr_number": 999,
        "pr_head_sha": SHA,
        "hud_projection": hud_proj,
        "hud_update_key": calculated_key,
        "session_lineage": ["session_parent_000", "session_jules_001"],
    }
    data.update(overrides)
    return JulesReport.model_validate(data)


def test_jules_report_hud_update_key_determinism():
    hud_proj = {"frontier": "test-frontier", "gate": "TEST_GATE"}
    key1 = compute_hud_projection_key(hud_proj)
    key2 = compute_hud_projection_key(hud_proj)
    assert key1 == key2
    assert len(key1) == 64

    # Report validation verifies key matches projection
    report = JulesReport.model_validate({
        "session_id": "sess_1",
        "report_id": "rep_1",
        "git_sha": SHA,
        "branch": "main",
        "status": "VERIFIED",
        "objective": "Obj",
        "summary": "Sum",
        "hud_projection": hud_proj,
        "hud_update_key": key1,
    })
    assert report.hud_update_key == key1

    # Mismatched key is rejected
    with pytest.raises(ValueError, match="hud_update_key does not match"):
        JulesReport.model_validate({
            "session_id": "sess_1",
            "report_id": "rep_1",
            "git_sha": SHA,
            "branch": "main",
            "status": "VERIFIED",
            "objective": "Obj",
            "summary": "Sum",
            "hud_projection": hud_proj,
            "hud_update_key": "bad_key",
        })


def test_field_c2_ingestion_carries_structured_hud_and_lineage():
    runtime = FakeRuntime()
    report = make_report_with_hud()
    result = ingest_jules_report(runtime, report, canonical_git_sha=SHA)

    assert result.accepted is True
    assert result.hud_update_key == report.hud_update_key
    assert result.field_c2_envelope["session_lineage"] == ["session_parent_000", "session_jules_001"]

    assert len(runtime.payloads) == 1
    memory = runtime.payloads[0].memories[0]
    content = memory["content"]
    assert content["hud_projection"] == report.hud_projection
    assert content["hud_update_key"] == report.hud_update_key
    assert content["session_lineage"] == ["session_parent_000", "session_jules_001"]
    assert content["field_c2_envelope"]["authority"] == "field_c2_jules_report"


def test_rehydrate_c2_from_jules_report_full_path():
    runtime = FakeRuntime()
    report = make_report_with_hud()

    immersion_state, response, result = rehydrate_c2_from_jules_report(
        runtime,
        report,
        canonical_git_sha=SHA,
        force_hud=True,
    )

    assert result.accepted is True
    assert immersion_state.frontier == "field-c2-handoff"
    assert immersion_state.gate == "GOVERNED_EXECUTION"
    assert immersion_state.flight_id == "C2:session_jules_001"

    rendered = response.render()
    # Prose report text preserved exactly
    assert "Completed Field-C2 to Tower-C2 structured handoff contract." in rendered
    # Immersion surfaces canonical renderer output with 5 established layers
    assert "01 — COMMAND BAND" in rendered
    assert "02 — OPERATING PICTURE" in rendered
    assert "03 — PROGRESSION / IMPACT" in rendered
    assert "04 — STRIKE FEED" in rendered
    assert "05 — ORGANISM PROGRESSION" in rendered
    assert "[SAGE::C2::CHATGPT]" in rendered


def test_changed_hud_surfaces_and_unchanged_hud_suppresses(tmp_path):
    from sage.experimental.airspace.manager import AirspaceManager
    from sage.experimental.airspace.models import StationID, XPCategory

    ledger_file = tmp_path / "ledger.json"
    mgr = AirspaceManager(ledger_file)
    runtime = FakeRuntime()
    report1 = make_report_with_hud()

    # First turn surfaces HUD (previous key is None)
    immersion_state1, response1, _ = rehydrate_c2_from_jules_report(
        runtime, report1, canonical_git_sha=SHA, organism_manager=mgr, previous_hud_update_key=None
    )
    key1 = response1.hud_update_key
    assert response1.should_render_hud is True

    # Same HUD on next turn without force suppresses HUD
    response2_same = rehydrate_c2_from_jules_report(
        runtime, report1, canonical_git_sha=SHA, organism_manager=mgr, previous_hud_update_key=key1, force_hud=False
    )[1]
    assert response2_same.should_render_hud is False

    # Changed HUD on next turn (e.g. state progression in manager) surfaces HUD
    mgr.award_xp(
        actor="C2",
        station_id=StationID.MISSION_CONTROL,
        category=XPCategory.MISSION_XP,
        amount=10,
        reason="Test progression change",
        verified_event_ref="ref-change-1",
    )
    response3_changed = rehydrate_c2_from_jules_report(
        runtime, report1, canonical_git_sha=SHA, organism_manager=mgr, previous_hud_update_key=key1, force_hud=False
    )[1]
    assert response3_changed.should_render_hud is True


def test_invalid_git_sha_mismatch_fails_closed():
    runtime = FakeRuntime()
    report = make_report_with_hud(git_sha=OTHER_SHA, pr_head_sha=OTHER_SHA)

    with pytest.raises(ValueError, match="Jules report rejected"):
        rehydrate_c2_from_jules_report(runtime, report, canonical_git_sha=SHA)

    assert runtime.payloads == []


def test_jules_report_rehydration_delegates_to_canonical_airspace_renderer():
    runtime = FakeRuntime()
    report = make_report_with_hud()

    _, response, result = rehydrate_c2_from_jules_report(
        runtime,
        report,
        canonical_git_sha=SHA,
        force_hud=True,
    )
    rendered = response.render()

    # Verify canonical AirspaceRenderer layers are present in order
    idx1 = rendered.index("01 — COMMAND BAND")
    idx2 = rendered.index("02 — OPERATING PICTURE")
    idx3 = rendered.index("03 — PROGRESSION / IMPACT")
    idx4 = rendered.index("04 — STRIKE FEED")
    idx5 = rendered.index("05 — ORGANISM PROGRESSION")

    assert idx1 < idx2 < idx3 < idx4 < idx5
    assert "Human Director" in rendered or "Jules" in rendered


def test_jules_prose_report_remains_untouched():
    runtime = FakeRuntime()
    custom_summary = "Exact unaltered Jules engineering summary text with markdown details."
    report = make_report_with_hud(summary=custom_summary)

    _, response, _ = rehydrate_c2_from_jules_report(
        runtime, report, canonical_git_sha=SHA, force_hud=True
    )
    env = build_response_envelope(response.body, c2_chatgpt_presentation())

    assert custom_summary in response.body
    assert custom_summary in env["response_text"]


def test_pasted_report_normalizes_transport_to_canonical_hud_presentation():
    """Verify input transport formats (e.g. code blocks or raw reports) are normalized to native HUD output."""
    runtime = FakeRuntime()
    # Pasted report transport containing code blocks or raw text formatting
    pasted_transport_summary = "```text\n01 — COMMAND BAND // PASTED HUD CODE BLOCK CONTAINER\n```\nReport analysis."
    report = make_report_with_hud(summary=pasted_transport_summary)

    _, response, result = rehydrate_c2_from_jules_report(
        runtime, report, canonical_git_sha=SHA, force_hud=True
    )
    rendered = response.render()

    # Native SAGE Hub visual surface is rendered without being wrapped as a code block
    assert "01 — COMMAND BAND" in rendered
    assert "02 — OPERATING PICTURE" in rendered
    assert "04 — STRIKE FEED" in rendered
    assert "[SAGE::C2::CHATGPT]" in rendered
    assert result.accepted is True
