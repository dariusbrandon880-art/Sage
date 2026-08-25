"""Unit tests for C2 Reconvergence Evidence Synthesizer & Promotion Gate."""

from sage.c2.reconvergence_synthesizer import (
    C2ReconvergenceSynthesizer,
    FlightExecutionSummary,
)


def test_reconvergence_synthesis_pass():
    synthesizer = C2ReconvergenceSynthesizer(wave_id="big-jump-wave-session-3")

    flights = [
        FlightExecutionSummary(
            flight_id=f"F{i}",
            target=f"target_{i}",
            classification="UNSTARTED",
            execution_result="PASS",
            exact_head="b44b892",
            tests_passed=10,
            evidence_ref=f"evidence_{i}.json",
            pr_or_change=f"PR #{i}",
        )
        for i in range(1, 6)
    ]

    package = synthesizer.synthesize_reconvergence(flights)

    assert package.wave_id == "big-jump-wave-session-3"
    assert package.total_flights == 5
    assert package.successful_flights == 5
    assert package.blocked_flights == 0
    assert package.first_pass_verification_rate == 100.0
    assert package.reconvergence_verdict == "PASS"
    assert len(package.package_hash) == 64


def test_reconvergence_synthesis_fail_closed_on_blocker():
    synthesizer = C2ReconvergenceSynthesizer(wave_id="big-jump-wave-session-3")

    flights = [
        FlightExecutionSummary(
            flight_id=f"F{i}",
            target=f"target_{i}",
            classification="UNSTARTED",
            execution_result="PASS",
            exact_head="b44b892",
            tests_passed=10,
            evidence_ref=f"evidence_{i}.json",
            pr_or_change=f"PR #{i}",
        )
        for i in range(1, 5)
    ]

    flights.append(
        FlightExecutionSummary(
            flight_id="F5",
            target="target_5",
            classification="UNSTARTED",
            execution_result="BLOCKED",
            exact_head="b44b892",
            tests_passed=0,
            evidence_ref="evidence_5.json",
            pr_or_change="N/A",
            blocker="Dependency missing",
        )
    )

    package = synthesizer.synthesize_reconvergence(flights)

    assert package.total_flights == 5
    assert package.successful_flights == 4
    assert package.blocked_flights == 1
    assert package.first_pass_verification_rate == 80.0
    assert package.reconvergence_verdict == "FAIL_CLOSED"
