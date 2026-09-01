import pytest

from sage.experimental.sagi_discovery_flight_selector import (
    DiscoveryCandidate,
    FlightRole,
    SAGIDiscoveryFlightSelector,
)


def candidate(i, role, score=1.0, safety=1.0, provenance=None):
    provenance_ref = f"research-{i}" if provenance is None else provenance
    return DiscoveryCandidate(
        str(i), f"candidate-{i}", role, score, score, score, safety, score,
        provenance_ref
    )


def test_selects_one_candidate_for_each_governed_role():
    candidates = tuple(candidate(i, role, i / 5) for i, role in enumerate(FlightRole, 1))
    proposal = SAGIDiscoveryFlightSelector().select(candidates, frontier_digest="frontier")
    assert len(proposal.candidates) == 5
    assert {c.role for c in proposal.candidates} == set(FlightRole)
    assert proposal.selection_digest


def test_missing_role_fails_closed():
    candidates = tuple(candidate(i, role) for i, role in enumerate(FlightRole) if role is not FlightRole.FALSIFICATION)
    with pytest.raises(ValueError, match="FALSIFICATION"):
        SAGIDiscoveryFlightSelector().select(candidates, frontier_digest="frontier")


def test_unsafe_candidates_are_not_selected():
    candidates = tuple(candidate(i, role, safety=0.0) for i, role in enumerate(FlightRole))
    with pytest.raises(ValueError):
        SAGIDiscoveryFlightSelector().select(candidates, frontier_digest="frontier")


def test_selection_requires_canonical_frontier_digest():
    candidates = tuple(candidate(i, role) for i, role in enumerate(FlightRole))
    with pytest.raises(ValueError):
        SAGIDiscoveryFlightSelector().select(candidates, frontier_digest="")


def test_candidate_provenance_is_required():
    candidates = tuple(candidate(i, role, provenance="") for i, role in enumerate(FlightRole))
    with pytest.raises(ValueError, match="provenance"):
        SAGIDiscoveryFlightSelector().select(candidates, frontier_digest="frontier")


def test_duplicate_candidate_ids_fail_closed():
    candidates = list(candidate(i, role) for i, role in enumerate(FlightRole))
    candidates[1] = candidate(0, FlightRole.INFORMATION_GAIN)
    with pytest.raises(ValueError, match="unique"):
        SAGIDiscoveryFlightSelector().select(tuple(candidates), frontier_digest="frontier")


def test_selection_digest_is_deterministic_and_tamper_detecting():
    candidates = tuple(candidate(i, role, i / 5) for i, role in enumerate(FlightRole, 1))
    selector = SAGIDiscoveryFlightSelector()
    first = selector.select(candidates, frontier_digest="frontier")
    second = selector.select(candidates, frontier_digest="frontier")
    assert first.selection_digest == second.selection_digest
    with pytest.raises(ValueError, match="digest"):
        selector.select(candidates, frontier_digest="frontier", selection_digest="tampered")


def test_selection_digest_binds_semantic_candidate_payload():
    candidates = tuple(candidate(i, role, i / 5) for i, role in enumerate(FlightRole, 1))
    selector = SAGIDiscoveryFlightSelector()
    baseline = selector.select(candidates, frontier_digest="frontier")

    tampered = list(candidates)
    original = tampered[0]
    tampered[0] = DiscoveryCandidate(
        original.candidate_id,
        "tampered description",
        original.role,
        original.consequentiality,
        original.information_gain,
        original.falsification_value,
        original.safety,
        original.evidence_gap,
        original.provenance_ref,
    )
    with pytest.raises(ValueError, match="digest"):
        selector.select(tuple(tampered), frontier_digest="frontier", selection_digest=baseline.selection_digest)


def test_non_governed_role_type_fails_closed():
    candidates = list(candidate(i, role) for i, role in enumerate(FlightRole))
    original = candidates[0]
    candidates[0] = DiscoveryCandidate(
        original.candidate_id,
        original.description,
        "CONSEQUENT_FRONTIER",
        original.consequentiality,
        original.information_gain,
        original.falsification_value,
        original.safety,
        original.evidence_gap,
        original.provenance_ref,
    )
    with pytest.raises(ValueError, match="FlightRole"):
        SAGIDiscoveryFlightSelector().select(tuple(candidates), frontier_digest="frontier")


def test_whitespace_frontier_digest_fails_closed():
    candidates = tuple(candidate(i, role) for i, role in enumerate(FlightRole))
    with pytest.raises(ValueError, match="frontier digest"):
        SAGIDiscoveryFlightSelector().select(candidates, frontier_digest="   ")


def test_generate_broad_surface_candidates():
    candidates = SAGIDiscoveryFlightSelector.generate_broad_surface_candidates()
    assert len(candidates) == 5
    roles = {c.role for c in candidates}
    assert roles == set(FlightRole)

    # Verify candidates span distinct SAGE capability surfaces
    descriptions = " ".join(c.description for c in candidates)
    assert "Observatory" in descriptions
    assert "Sports" in descriptions
    assert "SAGI" in descriptions
    assert "C2" in descriptions
    assert "Airspace" in descriptions

    proposal = SAGIDiscoveryFlightSelector().select(candidates, frontier_digest="broad-surface-frontier")
    assert len(proposal.candidates) == 5
    assert proposal.selection_digest
