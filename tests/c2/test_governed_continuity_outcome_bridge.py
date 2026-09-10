"""Unit and integration test suite for GovernedContinuityOutcomeBridge."""

import ast
import importlib
from pathlib import Path
import time

import pytest

from sage.c2.governed_continuity_outcome_bridge import (
    GovernedContinuityOutcomeBridge,
)
from sage.c2.mission_continuity import CANONICAL_MAIN_GOALS


@pytest.fixture
def bridge():
    return GovernedContinuityOutcomeBridge()


@pytest.fixture
def test_setup():
    lc_mod = importlib.import_module("sage.experimental.longitudinal_capability")
    p4_mod = importlib.import_module("sage.experimental.act.phase_4_eval")

    MissionCase = getattr(lc_mod, "MissionCase")
    FlightObservation = getattr(lc_mod, "FlightObservation")
    EvaluationPlan = getattr(lc_mod, "EvaluationPlan")

    PreExecutionBaseline = getattr(p4_mod, "PreExecutionBaseline")
    LearningIntervention = getattr(p4_mod, "LearningIntervention")
    PostExecutionObservation = getattr(p4_mod, "PostExecutionObservation")

    session_id = f"test_gco_sess_{int(time.time())}"

    missions = (
        MissionCase(mission_id="m_001_continuity", difficulty=1, requires_cross_session_reuse=True),
        MissionCase(mission_id="m_002_recovery", difficulty=2, requires_recovery=True),
    )
    plan = EvaluationPlan(
        evaluation_id="eval_gco_test_001",
        mission_set_id="mset_test_frontier",
        missions=missions,
        minimum_missions=2,
        minimum_relative_gain=0.10,
        maximum_regression_rate=0.0,
        minimum_evidence_completeness=1.0,
        minimum_provenance_preservation=1.0,
        minimum_unauthorized_block_rate=1.0,
        minimum_continuity_integrity=1.0,
        minimum_learning_candidate_quality=0.8,
    )

    baseline_obs = [
        FlightObservation(
            system="baseline",
            mission_id="m_001_continuity",
            session_id=session_id,
            success=False,
            evidence_complete=True,
            provenance_preserved=True,
            unauthorized_transition_blocked=True,
            continuity_intact=True,
            retained_across_sessions=True,
            learning_candidate_quality=0.5,
        ),
        FlightObservation(
            system="baseline",
            mission_id="m_002_recovery",
            session_id=session_id,
            success=False,
            evidence_complete=True,
            provenance_preserved=True,
            unauthorized_transition_blocked=True,
            continuity_intact=True,
            retained_across_sessions=True,
            learning_candidate_quality=0.5,
        ),
    ]

    sage_obs = [
        FlightObservation(
            system="sage",
            mission_id="m_001_continuity",
            session_id=session_id,
            success=True,
            evidence_complete=True,
            provenance_preserved=True,
            unauthorized_transition_blocked=True,
            continuity_intact=True,
            retained_across_sessions=True,
            learning_candidate_quality=0.95,
        ),
        FlightObservation(
            system="sage",
            mission_id="m_002_recovery",
            session_id=session_id,
            success=True,
            recovered_after_failure=True,
            evidence_complete=True,
            provenance_preserved=True,
            unauthorized_transition_blocked=True,
            continuity_intact=True,
            retained_across_sessions=True,
            learning_candidate_quality=0.92,
        ),
    ]

    fixture_id = "fix_test_gco_001"
    fixture_hash = "a1b2c3d4e5f67890123456789012345678901234567890123456789012345678"
    base_sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    rcpt_sha = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"

    now = time.time()
    t_base = now - 100
    t_interv = now - 50
    t_obs = now

    bench_baseline = PreExecutionBaseline(
        fixture_id=fixture_id,
        fixture_hash=fixture_hash,
        baseline_sha256=base_sha,
        baseline_score=0.65,
        timestamp=t_base,
    )

    bench_interv = LearningIntervention(
        fixture_id=fixture_id,
        intervention_id="interv_test_001",
        learning_signal_hash="signal_test_hash",
        timestamp=t_interv,
    )

    bench_observation = PostExecutionObservation(
        fixture_id=fixture_id,
        fixture_hash=fixture_hash,
        receipt_sha256=rcpt_sha,
        observed_score=0.95,
        timestamp=t_obs,
    )

    return {
        "session_id": session_id,
        "plan": plan,
        "baseline_obs": baseline_obs,
        "sage_obs": sage_obs,
        "bench_baseline": bench_baseline,
        "bench_interv": bench_interv,
        "bench_observation": bench_observation,
    }


def test_successful_3_stage_frontier_evaluation(bridge, test_setup):
    receipt = bridge.execute_frontier_evaluation(
        main_goals=CANONICAL_MAIN_GOALS,
        session_id=test_setup["session_id"],
        baseline_observations=test_setup["baseline_obs"],
        sage_observations=test_setup["sage_obs"],
        evaluation_plan=test_setup["plan"],
        benchmark_baseline=test_setup["bench_baseline"],
        benchmark_intervention=test_setup["bench_interv"],
        benchmark_observation=test_setup["bench_observation"],
    )

    assert receipt.continuity_status == "VERIFIED_INTACT"
    assert receipt.outcome_verdict == "PASS"
    assert receipt.relative_success_gain == 1.0
    assert receipt.benchmark_classification == "VALID_IMPROVEMENT"
    assert receipt.overall_frontier_verdict == "PASS"
    assert receipt.fail_closed_reasons == ()
    assert len(receipt.git_head_sha) == 40
    assert receipt.compute_hash() == receipt.to_dict()["receipt_hash"]


def test_continuity_alignment_failure_fails_closed(bridge, test_setup):
    invalid_goals = ("invalid_goal_outside_canonical_hierarchy",)
    receipt = bridge.execute_frontier_evaluation(
        main_goals=invalid_goals,
        session_id=test_setup["session_id"],
        baseline_observations=test_setup["baseline_obs"],
        sage_observations=test_setup["sage_obs"],
        evaluation_plan=test_setup["plan"],
        benchmark_baseline=test_setup["bench_baseline"],
        benchmark_intervention=test_setup["bench_interv"],
        benchmark_observation=test_setup["bench_observation"],
    )

    assert receipt.continuity_status == "CONTINUITY_FAILURE"
    assert receipt.overall_frontier_verdict == "NEGATIVE_RESULT"
    assert any("MISSION_CONTINUITY_ALIGNMENT_FAILURE" in r for r in receipt.fail_closed_reasons)


def test_outcome_regression_fails_closed(bridge, test_setup):
    lc_mod = importlib.import_module("sage.experimental.longitudinal_capability")
    FlightObservation = getattr(lc_mod, "FlightObservation")

    regressed_sage_obs = [
        FlightObservation(
            system="sage",
            mission_id="m_001_continuity",
            session_id=test_setup["session_id"],
            success=False,
            regression_detected=True,
            continuity_intact=False,
            retained_across_sessions=False,
        ),
        FlightObservation(
            system="sage",
            mission_id="m_002_recovery",
            session_id=test_setup["session_id"],
            success=False,
            regression_detected=True,
            continuity_intact=False,
            retained_across_sessions=False,
        ),
    ]

    receipt = bridge.execute_frontier_evaluation(
        main_goals=CANONICAL_MAIN_GOALS,
        session_id=test_setup["session_id"],
        baseline_observations=test_setup["baseline_obs"],
        sage_observations=regressed_sage_obs,
        evaluation_plan=test_setup["plan"],
        benchmark_baseline=test_setup["bench_baseline"],
        benchmark_intervention=test_setup["bench_interv"],
        benchmark_observation=test_setup["bench_observation"],
    )

    assert receipt.outcome_verdict == "NEGATIVE_RESULT"
    assert receipt.overall_frontier_verdict == "NEGATIVE_RESULT"
    assert any("OUTCOME_EVALUATION" in r for r in receipt.fail_closed_reasons)


def test_benchmark_invariant_violation_fails_closed(bridge, test_setup):
    p4_mod = importlib.import_module("sage.experimental.act.phase_4_eval")
    LearningIntervention = getattr(p4_mod, "LearningIntervention")

    invalid_interv = LearningIntervention(
        fixture_id=test_setup["bench_baseline"].fixture_id,
        intervention_id="interv_inv_001",
        learning_signal_hash="signal_hash",
        timestamp=test_setup["bench_baseline"].timestamp - 100.0,
    )

    receipt = bridge.execute_frontier_evaluation(
        main_goals=CANONICAL_MAIN_GOALS,
        session_id=test_setup["session_id"],
        baseline_observations=test_setup["baseline_obs"],
        sage_observations=test_setup["sage_obs"],
        evaluation_plan=test_setup["plan"],
        benchmark_baseline=test_setup["bench_baseline"],
        benchmark_intervention=invalid_interv,
        benchmark_observation=test_setup["bench_observation"],
    )

    assert receipt.benchmark_classification == "INVALID_EVALUATION"
    assert receipt.overall_frontier_verdict == "HOLD"
    assert any("BENCHMARK_VALIDATOR" in r for r in receipt.fail_closed_reasons)


def test_one_way_import_law_ast_compliance():
    """Verify no static imports from sage.experimental in the bridge."""
    bridge_file = Path("sage/c2/governed_continuity_outcome_bridge.py")
    assert bridge_file.exists(), "Bridge file must exist"

    tree = ast.parse(bridge_file.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert "sage.experimental" not in alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert "sage.experimental" not in node.module
