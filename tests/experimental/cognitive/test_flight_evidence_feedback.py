from sage.experimental.cognitive.flight_evidence_feedback import project_flight_evidence
from sage.experimental.longitudinal_capability import (
    CapabilityEvaluationReceipt,
    CapabilityVerdict,
)


def receipt(verdict, reasons=()):
    return CapabilityEvaluationReceipt(
        evaluation_id="eval", mission_set_id="missions", plan_hash="plan",
        baseline_metrics=(), sage_metrics=(), relative_success_gain=0.0,
        recovery_rate=0.0, regression_rate=0.0, verdict=verdict,
        fail_closed_reasons=tuple(reasons),
    )


def test_pass_projects_evidence_but_not_execution_authority():
    feedback = project_flight_evidence(receipt(CapabilityVerdict.PASS))
    assert feedback.validated_facts
    assert not feedback.forbidden_regressions
    assert "authority" in feedback.validated_facts[0].statement.lower()


def test_hold_does_not_manufacture_capability_memory():
    feedback = project_flight_evidence(receipt(CapabilityVerdict.HOLD, ["NO_GAIN"]))
    assert not feedback.validated_facts
    assert not feedback.forbidden_regressions


def test_negative_result_becomes_durable_forbidden_regression():
    feedback = project_flight_evidence(
        receipt(CapabilityVerdict.NEGATIVE_RESULT, ["REGRESSION_RATE_TOO_HIGH"])
    )
    assert not feedback.validated_facts
    assert len(feedback.forbidden_regressions) == 1
    assert feedback.forbidden_regressions[0].restricted_actions == ["REGRESSION_RATE_TOO_HIGH"]
    assert "CAPABILITY_QUALIFICATION" in feedback.forbidden_regressions[0].blocked_states


def test_projection_is_deterministic_for_same_receipt():
    source = receipt(CapabilityVerdict.NEGATIVE_RESULT, ["CONTINUITY_INTEGRITY_FAILURE"])
    assert project_flight_evidence(source) == project_flight_evidence(source)
