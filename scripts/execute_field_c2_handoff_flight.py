"""Execute real end-to-end Field-C2 → Tower-C2 handoff flight verification.

Validates the complete operational lifecycle:
Jules execution report -> Ingestion -> FieldC2ProjectionEnvelope -> Tower-C2 rehydration
-> HUD projection -> Immersion interface -> Continuity decision -> Prose preservation -> Receipt emission.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from sage.c2.jules_report_ingestion import (
    JulesReport,
    compute_hud_projection_key,
    rehydrate_c2_from_jules_report,
)
from sage.c2.response_envelope import build_response_envelope, c2_chatgpt_presentation
from sage.runtime.engine import SageRuntime


def get_current_head() -> str:
    res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def main():
    git_sha = get_current_head()

    # 1. Construct genuine Jules execution report with structured Field-C2 HUD projection
    hud_proj_v1 = {
        "frontier": "field-c2-operational-handoff",
        "gate": "GOVERNED_EXECUTION",
        "flight_id": "F1:jules_flight_2026",
        "phase": "EXECUTE",
        "trust_status": "VERIFIED",
    }
    key_v1 = compute_hud_projection_key(hud_proj_v1)

    prose_summary = (
        "Operationalized Field-C2 to Tower-C2 structured HUD handoff protocol across SAGE."
    )

    report_v1 = JulesReport(
        session_id="session_live_handoff_001",
        report_id="jules-report-live-001",
        git_sha=git_sha,
        branch="jules/field-c2-immersion-handoff-protocol",
        status="VERIFIED",
        objective="Verify live Field-C2 to Tower-C2 handoff flight",
        summary=prose_summary,
        evidence=["scripts/execute_field_c2_handoff_flight.py"],
        state_deltas={"frontier": "field-c2-operational-handoff"},
        pr_number=493,
        pr_head_sha=git_sha,
        hud_projection=hud_proj_v1,
        hud_update_key=key_v1,
        session_lineage=["session_root_000", "session_live_handoff_001"],
    )

    # 2. Execute rehydration flight turn 1 (Initial handoff)
    runtime = SageRuntime()
    immersion_state1, response1, ingestion1 = rehydrate_c2_from_jules_report(
        runtime, report_v1, canonical_git_sha=git_sha, previous_hud_update_key=None
    )

    assert ingestion1.accepted is True, "Ingestion must be accepted for matching Git HEAD"
    assert response1.should_render_hud is True, "First handoff must render the HUD surface"
    rendered_text1 = response1.render()
    assert prose_summary in rendered_text1, "Prose summary must be preserved intact"
    assert "01 — COMMAND BAND // SAGE MISSION CONTROL HUD" in rendered_text1, "HUD must surface"

    envelope1 = build_response_envelope(
        response1.body,
        c2_chatgpt_presentation(),
        field_c2_envelope=ingestion1.field_c2_envelope,
    )
    assert envelope1["field_c2_envelope"]["authority"] == "field_c2_jules_report"

    # 3. Execute rehydration flight turn 2 (Unchanged HUD - Continuity Suppression)
    actual_prev_key = response1.hud_update_key
    _, response2, ingestion2 = rehydrate_c2_from_jules_report(
        runtime, report_v1, canonical_git_sha=git_sha, previous_hud_update_key=actual_prev_key, force_hud=False
    )
    assert response2.should_render_hud is False, "Unchanged HUD must be suppressed by continuity contract"

    # 4. Execute rehydration flight turn 3 (Changed HUD - Surfacing)
    hud_proj_v2 = dict(hud_proj_v1)
    hud_proj_v2["frontier"] = "field-c2-next-frontier"
    key_v2 = compute_hud_projection_key(hud_proj_v2)

    report_v2 = JulesReport(
        session_id="session_live_handoff_001",
        report_id="jules-report-live-002",
        git_sha=git_sha,
        branch="jules/field-c2-immersion-handoff-protocol",
        status="VERIFIED",
        objective="Verify live Field-C2 changed HUD surfacing",
        summary="Advanced to next frontier via Field-C2 HUD update.",
        evidence=["scripts/execute_field_c2_handoff_flight.py"],
        state_deltas={"frontier": "field-c2-next-frontier"},
        pr_number=493,
        pr_head_sha=git_sha,
        hud_projection=hud_proj_v2,
        hud_update_key=key_v2,
        session_lineage=["session_root_000", "session_live_handoff_001"],
    )

    _, response3, ingestion3 = rehydrate_c2_from_jules_report(
        runtime, report_v2, canonical_git_sha=git_sha, previous_hud_update_key=key_v1, force_hud=False
    )
    assert response3.should_render_hud is True, "Changed HUD must surface on next turn"

    # 5. Fail-Closed Validation (Stale/Mismatched Git HEAD)
    stale_git_sha = "a" * 40
    stale_report = JulesReport(
        session_id="session_live_handoff_001",
        report_id="jules-report-stale-003",
        git_sha=stale_git_sha,
        branch="main",
        status="VERIFIED",
        objective="Stale SHA verification",
        summary="Stale report",
        pr_head_sha=stale_git_sha,
    )
    fail_closed_passed = False
    try:
        rehydrate_c2_from_jules_report(runtime, stale_report, canonical_git_sha=git_sha)
    except ValueError as exc:
        if "report Git SHA does not match canonical Git HEAD" in str(exc):
            fail_closed_passed = True

    assert fail_closed_passed is True, "Stale Git SHA must fail closed before rehydration"

    # 6. Emit Proof Receipt
    receipt = {
        "flight_id": "FIELD_C2_TOWER_C2_HANDOFF_FLIGHT_2026",
        "status": "VERIFIED",
        "canonical_git_sha": git_sha,
        "turn1_ingestion_accepted": ingestion1.accepted,
        "turn1_hud_key": key_v1,
        "turn1_hud_rendered": response1.should_render_hud,
        "turn2_hud_suppressed": not response2.should_render_hud,
        "turn3_changed_hud_rendered": response3.should_render_hud,
        "turn3_hud_key": key_v2,
        "fail_closed_stale_head_verified": fail_closed_passed,
        "prose_preserved": prose_summary in rendered_text1,
        "evidence_digest": ingestion1.evidence_digest,
        "field_c2_envelope_authority": envelope1["field_c2_envelope"]["authority"],
    }

    receipt_path = Path("evidence_capture/field_c2_handoff_receipt.json")
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print(f"[SAGE::C2::FLIGHT] Live Field-C2 → Tower-C2 handoff flight complete. Receipt written to {receipt_path}")


if __name__ == "__main__":
    main()
