from scripts.run_longitudinal_flight_002 import MISSIONS, PLAN


def test_flight_002_is_discriminative_and_observation_only():
    assert len(MISSIONS) == 4
    assert any(not mission.requires_cross_session_reuse for mission in MISSIONS)
    assert any(mission.requires_recovery for mission in MISSIONS)
    assert PLAN.minimum_relative_gain > 0
    assert PLAN.minimum_learning_candidate_quality == 0.0


def test_flight_002_plan_is_deterministic():
    assert PLAN.plan_hash() == PLAN.plan_hash()
