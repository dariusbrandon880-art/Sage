import pytest

from sage.experimental.sagi_discovery_flight_selector import (
    DiscoveryCandidate,
    FlightRole,
    SAGIDiscoveryFlightSelector,
)


def candidate(i, role, score=1.0):
    return DiscoveryCandidate(
        str(i), f"candidate-{i}", role, score, score, score, 1.0, score, f"research-{i}"
    )


def test_selects_one_candidate_for_each_governed_role():
    candidates = tuple(candidate(i, role, i) for i, role in enumerate(FlightRole, 1))
    proposal = SAGIDiscoveryFlightSelector().select(
        candidates, frontier_digest="frontier", selection_digest="selection"
    )
    assert len(proposal.candidates) == 5
    assert {c.role for c in proposal.candidates} == set(FlightRole)


def test_missing_role_fails_closed():
    candidates = tuple(candidate(i, role) for i, role in enumerate(FlightRole) if role is not FlightRole.FALSIFICATION)
    with pytest.raises(ValueError, match="FALSIFICATION"):
        SAGIDiscoveryFlightSelector().select(
            candidates, frontier_digest="frontier", selection_digest="selection"
        )


def test_unsafe_candidates_are_not_selected():
    candidates = tuple(
        DiscoveryCandidate(str(i), "x", role, 100, 100, 100, 0, 100, f"r{i}")
        for i, role in enumerate(FlightRole)
    )
    with pytest.raises(ValueError):
        SAGIDiscoveryFlightSelector().select(
            candidates, frontier_digest="frontier", selection_digest="selection"
        )


def test_selection_requires_canonical_digests():
    candidates = tuple(candidate(i, role) for i, role in enumerate(FlightRole))
    with pytest.raises(ValueError):
        SAGIDiscoveryFlightSelector().select(
            candidates, frontier_digest="", selection_digest="selection"
        )
