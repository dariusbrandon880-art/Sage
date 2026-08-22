from sage.experimental.longitudinal_capability import (
    CapabilityVerdict,
    EvaluationPlan,
    FlightObservation,
    LongitudinalCapabilityEvaluator,
    MissionCase,
)


def _plan():
    return EvaluationPlan(
        evaluation_id="LCF-001",
        mission_set_id="MISSION-SET-001",
        missions=(
            MissionCase("m1", 1),
            MissionCase("m2", 2, requires_recovery=True),
            MissionCase("m3", 3),
            MissionCase("m4", 4, requires_recovery=True),
        ),
        minimum_missions=4,
        minimum_relative_gain=0.20,
        maximum_regression_rate=0.0,
        minimum_evidence_completeness=1.0,
        minimum_provenance_preservation=1.0,
        minimum_unauthorized_block_rate=1.0,
        minimum_continuity_integrity=1.0,
        minimum_learning_candidate_quality=0.8,
    )


def _observation(system, mission_id, success=True, recovery=False, regression=False, session="s1"):
    return FlightObservation(
        system=system,
        mission_id=mission_id,
        session_id=session,
        success=success,
        recovered_after_failure=recovery,
        evidence_complete=True,
        provenance_preserved=True,
        unauthorized_transition_blocked=True,
        continuity_intact=True,
        retained_across_sessions=True,
        learning_candidate_quality=0.9,
        elapsed_seconds=10.0,
        cost_units=1.0,
        regression_detected=regression,
    )


def _suite(system, successes):
    return [
        _observation(
            system,
            f"m{i}",
            success=success,
            recovery=(i == 2 and system == "sage"),
            session=f"s{i}",
        )
        for i, success in enumerate(successes, 1)
    ]


def test_plan_hash_is_deterministic():
    assert _plan().plan_hash() == _plan().plan_hash()


def test_baseline_comparison_can_prove_positive_result():
    receipt = LongitudinalCapabilityEvaluator(_plan()).evaluate(
        _suite("baseline", [True, False, False, False]),
        _suite("sage", [True, True, True, True]),
    )
    assert receipt.verdict is CapabilityVerdict.PASS
    assert receipt.relative_success_gain == 3.0
    assert receipt.receipt_hash()


def test_missing_mission_fails_closed_before_verdict():
    try:
        LongitudinalCapabilityEvaluator(_plan()).evaluate(
            _suite("baseline", [True, True, True, True]),
            _suite("sage", [True, True, True]),
        )
    except ValueError as exc:
        assert "MISSION_SET_MISMATCH" in str(exc)
    else:
        raise AssertionError("expected mission-set mismatch")


def test_indeterminate_learning_quality_blocks_positive_verdict():
    sage = _suite("sage", [True, True, True, True])
    sage[-1] = _observation("sage", "m4", session="s4")
    sage[-1] = FlightObservation(**{**sage[-1].__dict__, "learning_candidate_quality": None})
    receipt = LongitudinalCapabilityEvaluator(_plan()).evaluate(
        _suite("baseline", [True, False, False, False]), sage
    )
    assert receipt.verdict is CapabilityVerdict.HOLD
    assert "LEARNING_CANDIDATE_QUALITY_INDETERMINATE" in receipt.fail_closed_reasons


def test_regression_is_negative_result_not_hold():
    sage = _suite("sage", [True, True, True, True])
    sage[-1] = FlightObservation(**{**sage[-1].__dict__, "regression_detected": True})
    receipt = LongitudinalCapabilityEvaluator(_plan()).evaluate(
        _suite("baseline", [True, False, False, False]), sage
    )
    assert receipt.verdict is CapabilityVerdict.NEGATIVE_RESULT
    assert "REGRESSION_RATE_TOO_HIGH" in receipt.fail_closed_reasons


def test_continuity_failure_is_negative_result():
    sage = _suite("sage", [True, True, True, True])
    sage[2] = FlightObservation(**{**sage[2].__dict__, "continuity_intact": False})
    receipt = LongitudinalCapabilityEvaluator(_plan()).evaluate(
        _suite("baseline", [True, False, False, False]), sage
    )
    assert receipt.verdict is CapabilityVerdict.NEGATIVE_RESULT
    assert "CONTINUITY_INTEGRITY_FAILURE" in receipt.fail_closed_reasons


def test_retention_failure_cannot_pass():
    sage = _suite("sage", [True, True, True, True])
    sage[0] = FlightObservation(**{**sage[0].__dict__, "retained_across_sessions": False})
    receipt = LongitudinalCapabilityEvaluator(_plan()).evaluate(
        _suite("baseline", [True, False, False, False]), sage
    )
    assert receipt.verdict is CapabilityVerdict.NEGATIVE_RESULT
    assert "CAPABILITY_RETENTION_FAILURE" in receipt.fail_closed_reasons


def test_duplicate_observation_is_rejected():
    baseline = _suite("baseline", [True, False, False, False])
    baseline.append(baseline[0])
    try:
        LongitudinalCapabilityEvaluator(_plan()).evaluate(
            baseline, _suite("sage", [True, True, True, True])
        )
    except ValueError as exc:
        assert "DUPLICATE_OBSERVATION" in str(exc)
    else:
        raise AssertionError("expected duplicate observation failure")


def test_evaluation_is_single_use():
    evaluator = LongitudinalCapabilityEvaluator(_plan())
    baseline = _suite("baseline", [True, False, False, False])
    sage = _suite("sage", [True, True, True, True])
    evaluator.evaluate(baseline, sage)
    try:
        evaluator.evaluate(baseline, sage)
    except RuntimeError as exc:
        assert "ALREADY_FINALIZED" in str(exc)
    else:
        raise AssertionError("expected single-use finalization failure")


def test_system_labels_are_not_interchangeable():
    baseline = _suite("baseline", [True, False, False, False])
    sage = _suite("baseline", [True, True, True, True])
    try:
        LongitudinalCapabilityEvaluator(_plan()).evaluate(baseline, sage)
    except ValueError as exc:
        assert "SAGE_SYSTEM_LABEL_MISMATCH" in str(exc)
    else:
        raise AssertionError("expected system label mismatch")


def test_invalid_input_does_not_consume_evaluation():
    evaluator = LongitudinalCapabilityEvaluator(_plan())
    try:
        evaluator.evaluate(
            _suite("baseline", [True, True, True, True]),
            _suite("sage", [True, True, True]),
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected validation failure")
    receipt = evaluator.evaluate(
        _suite("baseline", [True, False, False, False]),
        _suite("sage", [True, True, True, True]),
    )
    assert receipt.verdict is CapabilityVerdict.PASS
