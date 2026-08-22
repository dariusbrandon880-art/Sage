import pytest
from sage.experimental.longitudinal_capability import FlightObservation
from sage.experimental.longitudinal_reliability import assess_reliability


def test_reliability_requires_observations():
    with pytest.raises(ValueError, match="NO_OBSERVATIONS"):
        assess_reliability([])


def test_reliability_holds_on_regression():
    result = assess_reliability([FlightObservation(system="sage", mission_id="m", session_id="s", success=True, evidence_complete=True, provenance_preserved=True, continuity_intact=True, regression_detected=True)])
    assert result.regression_rate == 1.0
    assert result.verdict == "HOLD"


def test_reliability_passes_complete_clean_flight():
    result = assess_reliability([FlightObservation(system="sage", mission_id="m", session_id="s", success=True, evidence_complete=True, provenance_preserved=True, continuity_intact=True)])
    assert result.verdict == "PASS"
