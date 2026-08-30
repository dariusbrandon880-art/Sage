"""Unit tests for C2 Reconvergence Evidence Synthesizer & 5x4 Promotion Gate."""

from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
    LifecycleMilestoneRecord,
    LifecycleStage,
)

VALID_SHA = "a162dfd30fb3c933a50d067febd43095f27cb00d"


def test_reconvergence_synthesis_pass_with_20_cell_and_exact_sha():
    synthesizer = C2ReconvergenceSynthesizer(wave_id="big-jump-wave-session-3")

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

    package = synthesizer.synthesize_reconvergence(flights)

    assert package.wave_id == "big-jump-wave-session-3"
    assert package.total_flights == 5
    assert package.successful_flights == 5
    assert package.blocked_flights == 0
    assert package.first_pass_verification_rate == 100.0
    assert package.reconvergence_verdict == "PASS"
    assert len(package.advancement_matrix_20_cells) == 20
    assert all(package.advancement_matrix_20_cells.values())
    assert len(package.package_hash) == 64


def test_matrix_stage_breakdown():
    synthesizer = C2ReconvergenceSynthesizer(wave_id="wave_test_breakdown")
    summaries = []
    sha = "a" * 40
    for idx in range(1, 6):
        m1 = LifecycleMilestoneRecord(stage=LifecycleStage.INTAKE_RECON, passed=True, evidence_ref="ref1")
        m2 = LifecycleMilestoneRecord(stage=LifecycleStage.BOUNDED_BUILD, passed=True, evidence_ref="ref2")
        m3 = LifecycleMilestoneRecord(stage=LifecycleStage.VERIFY_PROOF, passed=True, evidence_ref="ref3")
        m4 = LifecycleMilestoneRecord(stage=LifecycleStage.WAREHOUSE_PROMOTE, passed=True, evidence_ref="ref4")
        summaries.append(
            FlightExecutionSummary(
                flight_id=f"FLIGHT-{idx}",
                target=f"target_{idx}",
                classification="ACTIVE",
                execution_result="PASS",
                exact_head=sha,
                tests_passed=5,
                evidence_ref="evidence_ref",
                pr_or_change="PR Change",
                lifecycle_milestones=[m1, m2, m3, m4],
            )
        )
    pkg = synthesizer.synthesize_reconvergence(summaries)
    breakdown = synthesizer.get_matrix_stage_breakdown(pkg)
    assert len(breakdown) == 4
    for stage_data in breakdown.values():
        assert stage_data["passed_count"] == 5
        assert stage_data["pass_rate"] == 100.0


def test_reconvergence_fails_closed_on_unstarted_or_short_sha():
    synthesizer = C2ReconvergenceSynthesizer(wave_id="big-jump-wave-session-3")

    # Unstarted classification + short SHA should fail closed
    flights = [
        FlightExecutionSummary(
            flight_id=f"F{i}",
            target=f"target_{i}",
            classification="UNSTARTED",
            execution_result="PASS",
            exact_head="b44b892",  # Short/unexpanded SHA
            tests_passed=10,
            evidence_ref=f"evidence_{i}.json",
            pr_or_change=f"PR #{i}",
        )
        for i in range(1, 6)
    ]

    package = synthesizer.synthesize_reconvergence(flights)

    assert package.total_flights == 5
    assert package.successful_flights == 0
    assert package.blocked_flights == 5
    assert package.first_pass_verification_rate == 0.0
    assert package.reconvergence_verdict == "FAIL_CLOSED"
