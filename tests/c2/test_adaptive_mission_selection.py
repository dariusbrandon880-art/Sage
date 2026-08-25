"""Unit tests for Adaptive Mission Selection Engine."""

from sage.c2.adaptive_mission_selection import AdaptiveMissionSelectionEngine
from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
)

VALID_SHA = "db2592167dba5eda4c024bba9202ff085d9c1d9b"


def test_adaptive_mission_selection_ranking():
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

    engine = AdaptiveMissionSelectionEngine()
    packet = engine.rank_candidate(
        candidate_id="cand-001",
        target="sage/c2/adaptive_mission_selection.py",
        base_priority=5.0,
        prior_wave_package=pkg,
    )

    assert packet.candidate_id == "cand-001"
    assert packet.rank_score == 15.0  # 5.0 + 100 * 0.1
    assert packet.is_authorized is False  # Unauthorized by default
    assert len(packet.reasons) == 2
