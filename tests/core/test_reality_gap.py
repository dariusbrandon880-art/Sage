import pytest

from sage.core.reality_gap import (
    RealityGapAssessment,
    RealityGapStatus,
    RealityGapValidationError,
)


def make_assessment(**overrides):
    values = {
        "decision_id": "decision-001",
        "context_id": "ctx-001",
        "t0_claim_ref": "claim-sha-001",
        "t0_sufficiency_ref": "sufficiency-sha-001",
        "t1_observation_ref": "observation-sha-001",
        "observed_at": "2026-08-21T20:00:00Z",
        "status": RealityGapStatus.ALIGNED,
        "rationale": "Observed outcome matches the declared claim.",
    }
    values.update(overrides)
    return RealityGapAssessment.assess(**values)


def test_replay_is_deterministic():
    assert make_assessment().assessment_digest == make_assessment().assessment_digest


@pytest.mark.parametrize("field", [
    "decision_id", "context_id", "t0_claim_ref", "t0_sufficiency_ref",
    "t1_observation_ref", "observed_at", "rationale",
])
def test_missing_required_fields_fail_closed(field):
    with pytest.raises(RealityGapValidationError):
        make_assessment(**{field: ""})


def test_status_is_part_of_digest():
    aligned = make_assessment(status=RealityGapStatus.ALIGNED)
    diverged = make_assessment(status=RealityGapStatus.DIVERGED)
    assert aligned.assessment_digest != diverged.assessment_digest


def test_context_substitution_changes_digest():
    a = make_assessment(context_id="ctx-a")
    b = make_assessment(context_id="ctx-b")
    assert a.assessment_digest != b.assessment_digest


def test_t1_observation_substitution_changes_digest():
    a = make_assessment(t1_observation_ref="obs-a")
    b = make_assessment(t1_observation_ref="obs-b")
    assert a.assessment_digest != b.assessment_digest


def test_authority_is_never_granted():
    assessment = make_assessment(status=RealityGapStatus.DIVERGED)
    assert assessment.authority_granted is False
    assert assessment.to_dict()["authority_granted"] is False


def test_all_statuses_are_supported():
    for status in RealityGapStatus:
        assert make_assessment(status=status).status is status


def test_invalid_status_fails_closed():
    with pytest.raises(RealityGapValidationError):
        make_assessment(status="ALIGNED")


def test_public_projection_is_deterministic_and_complete():
    assessment = make_assessment()
    projection = assessment.to_dict()
    assert projection["status"] == "ALIGNED"
    assert projection["assessment_digest"] == assessment.assessment_digest
    assert set(projection) == {
        "decision_id", "context_id", "t0_claim_ref", "t0_sufficiency_ref",
        "t1_observation_ref", "observed_at", "status", "rationale",
        "assessment_digest", "authority_granted",
    }
