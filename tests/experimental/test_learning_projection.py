from sage.experimental.longitudinal_capability import CapabilityVerdict, FlightObservation
from sage.experimental.learning_projection import project_learning


def observation(**kwargs):
    defaults = dict(system="sage", mission_id="m", session_id="s", success=True, evidence_complete=True, provenance_preserved=True, continuity_intact=True)
    defaults.update(kwargs)
    return FlightObservation(**defaults)


def test_pass_creates_candidate_only_with_bound_evidence():
    result = project_learning(CapabilityVerdict.PASS, [observation()])
    assert result[0].kind == "CANDIDATE"
    assert result[0].candidate is True


def test_hold_creates_no_learning():
    result = project_learning(CapabilityVerdict.HOLD, [observation()])
    assert result[0].candidate is False


def test_negative_result_becomes_constraint():
    result = project_learning(CapabilityVerdict.NEGATIVE_RESULT, [observation(success=False)])
    assert result[0].kind == "NEGATIVE_CONSTRAINT"
    assert result[0].candidate is False
