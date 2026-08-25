"""Unit tests for C2 Wave Playbook Engine & Lifecycle Integration."""

from sage.c2.c2_wave_playbook import C2WavePlaybookEngine
from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
)

VALID_SHA = "db2592167dba5eda4c024bba9202ff085d9c1d9b"


def test_wave_playbook_evaluation_success():
    synthesizer = C2ReconvergenceSynthesizer(wave_id="big-jump-wave-session-4")

    flights = []
    for i in range(1, 6):
        milestones = [
            LifecycleMilestoneRecord(stage=LifecycleStage.INTAKE_RECON, passed=True, evidence_ref=f"ref_{i}_1"),
            LifecycleMilestoneRecord(stage=LifecycleStage.BOUNDED_BUILD, passed=True, evidence_ref=f"ref_{i}_2"),
            LifecycleMilestoneRecord(stage=LifecycleStage.VERIFY_PROOF, passed=True, evidence_ref=f"ref_{i}_3"),
            LifecycleMilestoneRecord(stage=LifecycleStage.WAREHOUSE_PROMOTE, passed=True, evidence_ref=f"ref_{i}_4"),
        ]
        flights.append(
            FlightExecutionSummary(
                flight_id=f"F{i}",
                target=f"target_{i}",
                classification="ACTIVE",
                execution_result="PASS",
                exact_head=VALID_SHA,
                tests_passed=10,
                evidence_ref=f"evidence_{i}.json",
                pr_or_change=f"PR #{i}",
                lifecycle_milestones=milestones,
            )
        )

    pkg = synthesizer.synthesize_reconvergence(flights)

    engine = C2WavePlaybookEngine()
    receipt = engine.evaluate_wave_package(pkg)

    assert receipt.playbook_name == "BigJumpWaveCanonicalPlaybook"
    assert receipt.wave_id == "big-jump-wave-session-4"
    assert receipt.total_cells_evaluated == 20
    assert receipt.cells_passed == 20
    assert receipt.first_pass_rate == 100.0
    assert len(receipt.receipt_hash) == 64
