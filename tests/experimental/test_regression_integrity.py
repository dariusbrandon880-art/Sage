from sage.experimental.longitudinal_capability import FlightObservation
from sage.experimental.regression_integrity import compare_observations


def obs(mid, success):
    return FlightObservation(system="sage", mission_id=mid, session_id="s", success=success)


def test_regression_is_detected_deterministically():
    result = compare_observations([obs("a", True), obs("b", True)], [obs("a", False), obs("b", True)])
    assert result.regressions == 1
    assert result.regression_rate == 0.5
    assert result.verdict == "REGRESSION"


def test_identical_trajectory_has_no_regression():
    result = compare_observations([obs("a", True)], [obs("a", True)])
    assert result.regressions == 0
    assert result.verdict == "NO_REGRESSION"
