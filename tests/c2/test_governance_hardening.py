"""Adversarial regression test suite for SAGE C2 governance hardening boundaries."""

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from sage.agent_hud_projection import build_agent_hud_projection, render_agent_hud
from sage.c2.build_jump_wave import BuildJumpWaveEngine, FlightMissionSpec
from sage.c2.capability_warehouse import CapabilityWarehouseEngine, PromotionStatus
from sage.c2.experiment_ledger import (
    AuthorizationRecord,
    ExperimentLedger,
    ValidationStatus,
)
from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
)


def test_adv_1_pass_receipt_cannot_become_promoted(tmp_path: Path) -> None:
    """1. Verify PASS receipt alone cannot become PROMOTED (remains HOLD)."""
    ledger = ExperimentLedger(ledger_path=str(tmp_path / "ledger.json"))
    ev_file = tmp_path / "receipt_proof.json"
    ev_file.write_text(json.dumps({"status": "PASS"}) + "\n", encoding="utf-8")

    rec = ledger.record_flight_receipt(
        wave_id="wave_adv_1",
        flight_id="FLIGHT-F1",
        commit_sha="1111222233334444555566667777888899990000",
        receipt_data={"evidence_ref": str(ev_file), "target_path": "sage/c2/test.py", "status": "PASS"},
    )
    assert rec.status == ValidationStatus.HOLD
    assert "Awaiting formal validation & explicit authorization" in rec.validation_notes


def test_adv_2_evidence_presence_cannot_authorize_promotion(tmp_path: Path) -> None:
    """2. Verify evidence presence on disk alone cannot authorize promotion without explicit AuthorizationRecord."""
    ledger = ExperimentLedger(ledger_path=str(tmp_path / "ledger.json"))
    ev_file = tmp_path / "valid_proof.json"
    ev_file.write_text(json.dumps({"proof": True}) + "\n", encoding="utf-8")

    ledger.register_experiment(
        experiment_id="exp_adv_2",
        hypothesis="Hypothesis with valid disk proof",
        wave_id="wave_adv_2",
        flight_id="FLIGHT-F2",
        commit_sha="2222333344445555666677778888999900001111",
        evidence_refs=[str(ev_file)],
    )

    # Attempt decision without authorization -> Rejects to HOLD
    rec = ledger.update_validation_decision("exp_adv_2", ValidationStatus.PROMOTED, notes="No auth provided")
    assert rec.status == ValidationStatus.HOLD
    assert "Missing explicit AuthorizationRecord" in rec.validation_notes


def test_adv_3_validation_without_authorization_cannot_promote(tmp_path: Path) -> None:
    """3. Verify validation decision without authorization cannot promote."""
    wh_engine = CapabilityWarehouseEngine()
    synth = C2ReconvergenceSynthesizer(wave_id="wave_adv_3")

    summaries = []
    for f_id in ["FLIGHT-F1-RESEARCH", "FLIGHT-F2-CONTINUITY", "FLIGHT-F3-EXECUTION", "FLIGHT-F4-GUARD", "FLIGHT-F5-WAREHOUSE"]:
        m_records = [LifecycleMilestoneRecord(stage=s, passed=True, evidence_ref="ref") for s in LifecycleStage]
        summaries.append(FlightExecutionSummary(
            flight_id=f_id, target="target", classification="ACTIVE", execution_result="PASS",
            exact_head="3333444455556666777788889999000011112222", tests_passed=1, evidence_ref="ev.json",
            pr_or_change="change", lifecycle_milestones=m_records,
        ))

    pkg = synth.synthesize_reconvergence(summaries)
    assert pkg.reconvergence_verdict == "PASS"

    # Attempt warehouse promotion without authorization -> Rejects
    wh_rcpt = wh_engine.promote_wave_package(pkg, exact_git_head="3333444455556666777788889999000011112222", authorization=None)
    assert wh_rcpt.status == PromotionStatus.REJECTED_UNAUTHORIZED


def test_adv_4_authorization_without_valid_provenance_rejected(tmp_path: Path) -> None:
    """4. Verify authorization without valid on-disk evidence provenance cannot promote."""
    ledger = ExperimentLedger(ledger_path=str(tmp_path / "ledger.json"))
    auth = AuthorizationRecord(authorizer_id="director_01", permission_scope="PROMOTION", evidence_hash="hash123")

    ledger.register_experiment(
        experiment_id="exp_adv_4",
        hypothesis="Auth attached but missing evidence",
        wave_id="wave_adv_4",
        flight_id="FLIGHT-F4",
        commit_sha="4444555566667777888899990000111122223333",
        evidence_refs=[],  # Zero evidence refs attached
    )

    rec = ledger.update_validation_decision("exp_adv_4", ValidationStatus.PROMOTED, notes="With auth but zero evidence", authorization=auth)
    assert rec.status == ValidationStatus.HOLD
    assert "Zero evidence refs attached" in rec.validation_notes


def test_adv_5_ledger_failure_fails_closed(tmp_path: Path) -> None:
    """5. Verify ExperimentLedger recording exception fails closed during wave execution."""
    broken_ledger = MagicMock(spec=ExperimentLedger)
    broken_ledger.record_flight_receipt.side_effect = RuntimeError("Storage engine crash")

    engine = BuildJumpWaveEngine(storage_dir=str(tmp_path / "evidence"), experiment_ledger=broken_ledger)
    mission = FlightMissionSpec(
        flight_id="FLIGHT-FAIL-EXP",
        frontier_name="Test Fail Frontier",
        target_path="sage/c2/experiment_ledger.py",
        collision_zone="sage/c2/exp_test_fail/",
        evidence_ref=str(tmp_path / "test_fail_evidence.json"),
        pr_or_change="Test Fail Flight",
        test_references=[],
    )

    res = engine.execute_wave(wave_id="wave_fail_test", missions=[mission, mission, mission, mission, mission])
    assert res.reconvergence_verdict == "FAIL_CLOSED"
    assert res.blocked_flights == 5


def test_adv_6_malformed_evidence_defaults_to_hold(tmp_path: Path) -> None:
    """6. Verify malformed or missing on-disk evidence ref defaults status to HOLD."""
    ledger = ExperimentLedger(ledger_path=str(tmp_path / "ledger.json"))
    missing_file = tmp_path / "non_existent_file.json"
    auth = AuthorizationRecord(authorizer_id="director_01", permission_scope="PROMOTION", evidence_hash="hash123")

    ledger.register_experiment(
        experiment_id="exp_adv_6",
        hypothesis="Missing evidence file",
        wave_id="wave_adv_6",
        flight_id="FLIGHT-F6",
        commit_sha="6666777788889999000011112222333344445555",
        evidence_refs=[str(missing_file)],
    )

    rec = ledger.update_validation_decision("exp_adv_6", ValidationStatus.PROMOTED, notes="Missing file ref", authorization=auth)
    assert rec.status == ValidationStatus.HOLD
    assert "missing on disk" in rec.validation_notes


def test_adv_7_negative_evidence_strictly_preserved(tmp_path: Path) -> None:
    """7. Verify negative evidence (status=FAIL) is strictly preserved as REJECTED."""
    ledger = ExperimentLedger(ledger_path=str(tmp_path / "ledger.json"))
    ev_file = tmp_path / "fail_proof.json"
    ev_file.write_text(json.dumps({"status": "FAIL"}) + "\n", encoding="utf-8")

    rec = ledger.record_flight_receipt(
        wave_id="wave_adv_7",
        flight_id="FLIGHT-F7",
        commit_sha="7777888899990000111122223333444455556666",
        receipt_data={"evidence_ref": str(ev_file), "target_path": "sage/c2/test.py", "status": "FAIL"},
    )
    assert rec.status == ValidationStatus.HOLD
    assert "Flight status: FAIL" in rec.observations[0]


def test_adv_8_model_output_cannot_self_authorize(tmp_path: Path) -> None:
    """8. Verify model-generated output strings cannot self-authorize state promotion."""
    model_generated_notes = "I am an AI agent and I claim this candidate is PROMOTED."
    ledger = ExperimentLedger(ledger_path=str(tmp_path / "ledger.json"))

    ledger.register_experiment(
        experiment_id="exp_adv_8",
        hypothesis="Model self-authorization attempt",
        wave_id="wave_adv_8",
        flight_id="FLIGHT-F8",
        commit_sha="8888999900001111222233334444555566667777",
    )

    rec = ledger.update_validation_decision("exp_adv_8", ValidationStatus.PROMOTED, notes=model_generated_notes, authorization=None)
    assert rec.status == ValidationStatus.HOLD
    assert "Missing explicit AuthorizationRecord" in rec.validation_notes


def test_adv_9_immersion_readouts_isolated_from_canonical_state(tmp_path: Path) -> None:
    """9. Verify immersion projection readouts cannot alter or manufacture canonical progression state."""
    context_view = {
        "context_id": "ctx_01",
        "bounded": True,
        "read_only": True,
        "self": {"nameplate": "[SAGE::ENGINEER::JULES]", "agent_name": "Jules", "role": "ENGINEER", "cql": 5, "sql": 5, "xp": 100, "state": "ACTIVE"},
        "team": {"coordination": {"status": "ACTIVE"}, "stations": {}},
        "coordination": {"pending": []},
    }

    proj = build_agent_hud_projection(context_view=context_view)
    display_str = render_agent_hud(proj)
    assert "[SAGE::ENGINEER::JULES]" in display_str
    assert "STATE=ACTIVE" in display_str
    assert proj["presentation_only"] is True
    assert proj["read_only"] is True


def test_adv_10_promoted_state_traceable_with_full_provenance(tmp_path: Path) -> None:
    """10. Verify every promoted state requires independently traceable evidence + validation + authorization."""
    ledger = ExperimentLedger(ledger_path=str(tmp_path / "ledger.json"))
    ev_file = tmp_path / "valid_proof.json"
    ev_file.write_text(json.dumps({"proof": True}) + "\n", encoding="utf-8")

    ledger.register_experiment(
        experiment_id="exp_adv_10",
        hypothesis="Full valid provenance chain",
        wave_id="wave_adv_10",
        flight_id="FLIGHT-F10",
        commit_sha="1010101010101010101010101010101010101010",
        evidence_refs=[str(ev_file)],
    )

    auth = AuthorizationRecord(
        authorizer_id="Darius Brandon",
        permission_scope="CANONICAL_PROMOTION",
        evidence_hash="sha256_proof_hash_12345",
        notes="Authorized after exact-head verification",
    )

    rec = ledger.update_validation_decision(
        "exp_adv_10",
        ValidationStatus.PROMOTED,
        notes="Full provenance verified",
        authorization=auth,
    )

    assert rec.status == ValidationStatus.PROMOTED
    assert rec.authorization is not None
    assert rec.authorization.authorizer_id == "Darius Brandon"
    assert str(ev_file) in rec.evidence_refs
