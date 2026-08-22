from sage.experimental.cross_flight_learning import FlightLearning, project_learning_candidates


def test_verified_learning_projects_as_noncanonical_candidate():
    candidates = project_learning_candidates(
        [FlightLearning("A", "L2", "reusable fix", "digest", True)],
        "B",
    )
    assert len(candidates) == 1
    assert candidates[0].authority_granted is False
    assert candidates[0].canonical is False


def test_unverified_learning_is_not_projected():
    candidates = project_learning_candidates(
        [FlightLearning("A", "L1", "unsupported", "digest", False)],
        "B",
    )
    assert candidates == ()


def test_same_mission_learning_is_not_cross_flight():
    candidates = project_learning_candidates(
        [FlightLearning("A", "L1", "local", "digest", True)],
        "A",
    )
    assert candidates == ()
