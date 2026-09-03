import pytest

from sage.experimental.airspace.career_calibration import (
    CalibrationEvent,
    IncreasingDeltaCurve,
    PiecewiseBandCurve,
    Profile,
    PromotionInputs,
    HybridCurve,
    evaluate_readiness,
    profile_events,
    replay_events,
    summarize_profiles,
)
from sage.experimental.airspace.points_xp_economy import PointEventType


def test_replay_uses_canonical_points_to_xp_conversion():
    replay = replay_events((CalibrationEvent("build", PointEventType.BUILD, volume=2),))
    assert replay[-1].cumulative_xp == replay[-1].cumulative_points // 10
    assert replay[-1].cumulative_points > 0


def test_replay_preserves_event_order_and_volume():
    replay = replay_events((
        CalibrationEvent("recon", PointEventType.RECON, volume=2),
        CalibrationEvent("build", PointEventType.BUILD, volume=1),
    ))
    assert [step.event_id for step in replay] == ["recon", "recon", "build"]
    assert replay[-1].cumulative_points == sum(step.points for step in replay)


def test_increasing_delta_curve_is_monotonic():
    curve = IncreasingDeltaCurve(start_threshold=10, first_delta=5, delta_growth=2)
    values = curve.thresholds(1, 30)
    assert len(values) == 30
    assert all(b > a for a, b in zip(values, values[1:]))


def test_piecewise_band_curve_is_monotonic():
    curve = PiecewiseBandCurve(start_threshold=10, band_deltas=(2, 3, 4, 5, 6, 7))
    values = curve.thresholds(1, 30)
    assert all(b > a for a, b in zip(values, values[1:]))


def test_hybrid_rejects_non_monotonic_corrections():
    base = IncreasingDeltaCurve(start_threshold=10, first_delta=5, delta_growth=1)
    curve = HybridCurve(base=base, corrections={3: -20})
    with pytest.raises(ValueError, match="non-monotonic"):
        curve.thresholds(1, 5)


def test_xp_threshold_alone_does_not_make_promotion_eligible():
    result = evaluate_readiness(PromotionInputs(1, 2, 100, 50, False, True))
    assert result.xp_threshold_reached is True
    assert result.eligible is False
    assert "qualification" in result.reason


def test_missing_evidence_holds_candidate():
    result = evaluate_readiness(PromotionInputs(1, 2, 100, 50, True, False))
    assert result.eligible is False
    assert "evidence" in result.reason


def test_rank_skipping_holds_candidate():
    result = evaluate_readiness(PromotionInputs(1, 3, 100, 50, True, True))
    assert result.eligible is False
    assert "sequential" in result.reason


def test_fully_satisfied_research_inputs_can_be_reported_ready():
    result = evaluate_readiness(PromotionInputs(1, 2, 100, 50, True, True))
    assert result.xp_threshold_reached is True
    assert result.eligible is True


def test_all_required_profiles_are_deterministic_simulation_inputs():
    summary = summarize_profiles()
    assert set(summary) == {profile.value for profile in Profile}
    assert all(row["verified_events"] > 0 for row in summary.values())
    assert all(row["verified_points"] >= row["career_xp"] * 10 for row in summary.values())


def test_profile_inputs_are_explicitly_event_mixed():
    elite = profile_events(Profile.ELITE)
    assert any(event.event_type == PointEventType.BOSS_CAPTURE for event in elite)
    assert any(event.event_type == PointEventType.BUILD for event in elite)
