import pytest
from sage.core.reality_gap import RealityGapAssessment, RealityGapStatus, RealityGapValidationError


def make(**overrides):
    data = dict(decision_id="d", context_id="c", t0_claim_ref="claim", t0_sufficiency_ref="sufficient", t1_observation_ref="obs", observed_at="2026-08-22T00:00:00Z", status=RealityGapStatus.ALIGNED, rationale="match")
    data.update(overrides)
    return RealityGapAssessment(**data)


def test_replay_is_deterministic():
    assert make().assessment_digest == make().assessment_digest

@pytest.mark.parametrize("field", ["decision_id", "context_id", "t0_claim_ref", "t0_sufficiency_ref", "t1_observation_ref", "observed_at", "rationale"])
def test_missing_field_fails_closed(field):
    with pytest.raises(RealityGapValidationError):
        make(**{field: ""})


def test_substitution_changes_digest():
    assert make(context_id="a").assessment_digest != make(context_id="b").assessment_digest
    assert make(t1_observation_ref="a").assessment_digest != make(t1_observation_ref="b").assessment_digest


def test_status_and_authority_boundaries():
    assert make(status=RealityGapStatus.DIVERGED).authority_granted is False
    with pytest.raises(RealityGapValidationError):
        make(status="ALIGNED")


def test_all_statuses_supported():
    assert {make(status=s).status for s in RealityGapStatus} == set(RealityGapStatus)
