"""Unit tests for sage.c2.frontier_intelligence_bridge."""

from __future__ import annotations

import pytest

from sage.c2.frontier_intelligence_bridge import (
    AuthorizedCandidate,
    FrontierIntelligenceBridge,
    compute_bridge_provenance_hash,
)
from sage.experimental.sagi_discovery_flight_selector import (
    DiscoveryCandidate,
    FlightRole,
    FlightSelectionProposal,
    SAGIDiscoveryFlightSelector,
)


def make_sample_candidates() -> tuple[DiscoveryCandidate, ...]:
    return (
        DiscoveryCandidate(
            candidate_id="cand_consequent",
            description="Consequent frontier candidate",
            role=FlightRole.CONSEQUENT_FRONTIER,
            consequentiality=0.9,
            information_gain=0.8,
            falsification_value=0.7,
            safety=0.95,
            evidence_gap=0.6,
            provenance_ref="ref_consequent_001",
        ),
        DiscoveryCandidate(
            candidate_id="cand_info_gain",
            description="Information gain candidate",
            role=FlightRole.INFORMATION_GAIN,
            consequentiality=0.8,
            information_gain=0.95,
            falsification_value=0.6,
            safety=0.9,
            evidence_gap=0.5,
            provenance_ref="ref_info_002",
        ),
        DiscoveryCandidate(
            candidate_id="cand_falsification",
            description="Falsification candidate",
            role=FlightRole.FALSIFICATION,
            consequentiality=0.7,
            information_gain=0.7,
            falsification_value=0.9,
            safety=0.85,
            evidence_gap=0.4,
            provenance_ref="ref_falsify_003",
        ),
        DiscoveryCandidate(
            candidate_id="cand_recovery",
            description="Recovery regression candidate",
            role=FlightRole.RECOVERY_REGRESSION,
            consequentiality=0.85,
            information_gain=0.75,
            falsification_value=0.8,
            safety=0.9,
            evidence_gap=0.5,
            provenance_ref="ref_recovery_004",
        ),
        DiscoveryCandidate(
            candidate_id="cand_transfer",
            description="Independent transfer candidate",
            role=FlightRole.INDEPENDENT_TRANSFER,
            consequentiality=0.75,
            information_gain=0.8,
            falsification_value=0.65,
            safety=0.92,
            evidence_gap=0.45,
            provenance_ref="ref_transfer_005",
        ),
    )


def test_frontier_intelligence_bridge_success():
    candidates = make_sample_candidates()
    selector = SAGIDiscoveryFlightSelector()
    proposal = selector.select(candidates, frontier_digest="frontier_digest_abc_123")

    authorized_map = {
        c.candidate_id: AuthorizedCandidate(
            candidate_id=c.candidate_id,
            authorized=True,
            authorized_by="c2_operator_001",
            authorization_token="auth_token_xyz_999",
        )
        for c in candidates
    }

    bridge = FrontierIntelligenceBridge(commit_sha="test_commit_sha_555")
    receipt = bridge.adapt_and_dispatch(proposal, authorized_map)

    assert receipt.bridge_verdict == "PASS"
    assert receipt.commit_sha == "test_commit_sha_555"
    assert receipt.frontier_digest == "frontier_digest_abc_123"
    assert len(receipt.authorized_candidate_ids) == 5
    assert not receipt.unauthorized_candidate_ids
    assert receipt.dispatch_receipt is not None
    assert receipt.dispatch_receipt["wave_verdict"] == "PASS"

    expected_hash = compute_bridge_provenance_hash(
        proposal.selection_digest,
        proposal.frontier_digest,
        receipt.authorized_candidate_ids,
        "test_commit_sha_555",
    )
    assert receipt.provenance_hash == expected_hash


def test_unauthorized_candidate_fails_closed():
    candidates = make_sample_candidates()
    selector = SAGIDiscoveryFlightSelector()
    proposal = selector.select(candidates, frontier_digest="frontier_digest_abc_123")

    # Authorize only 4 out of 5 candidates
    authorized_map = {
        c.candidate_id: AuthorizedCandidate(
            candidate_id=c.candidate_id,
            authorized=True,
            authorized_by="c2_operator_001",
            authorization_token="auth_token_xyz_999",
        )
        for c in candidates[:-1]
    }

    bridge = FrontierIntelligenceBridge(commit_sha="test_commit_sha_555")
    with pytest.raises(PermissionError, match="Frontier Intelligence Gate Violation"):
        bridge.adapt_and_dispatch(proposal, authorized_map)


def test_mismatched_selection_digest_fails_closed():
    candidates = make_sample_candidates()
    selector = SAGIDiscoveryFlightSelector()
    proposal = selector.select(candidates, frontier_digest="frontier_digest_abc_123")

    # Tamper with selection_digest
    tampered_proposal = FlightSelectionProposal(
        candidates=proposal.candidates,
        frontier_digest=proposal.frontier_digest,
        selection_digest="tampered_digest_fake_123",
    )

    authorized_map = {
        c.candidate_id: AuthorizedCandidate(
            candidate_id=c.candidate_id,
            authorized=True,
            authorized_by="c2_operator_001",
            authorization_token="auth_token_xyz_999",
        )
        for c in candidates
    }

    bridge = FrontierIntelligenceBridge(commit_sha="test_commit_sha_555")
    with pytest.raises(ValueError, match="Selection digest mismatch"):
        bridge.adapt_and_dispatch(tampered_proposal, authorized_map)


def test_unsafe_candidate_fails_closed():
    candidates = list(make_sample_candidates())
    # Set one candidate safety to 0.0
    candidates[0] = DiscoveryCandidate(
        candidate_id="cand_consequent",
        description="Unsafe candidate",
        role=FlightRole.CONSEQUENT_FRONTIER,
        consequentiality=0.9,
        information_gain=0.8,
        falsification_value=0.7,
        safety=0.0,
        evidence_gap=0.6,
        provenance_ref="ref_consequent_001",
    )

    # Use valid proposal structure
    proposal = FlightSelectionProposal(
        candidates=tuple(candidates),
        frontier_digest="frontier_digest_abc_123",
        selection_digest=SAGIDiscoveryFlightSelector._digest(
            tuple(candidates), "frontier_digest_abc_123"
        ),
    )

    authorized_map = {
        c.candidate_id: AuthorizedCandidate(
            candidate_id=c.candidate_id,
            authorized=True,
            authorized_by="c2_operator_001",
            authorization_token="auth_token_xyz_999",
        )
        for c in candidates
    }

    bridge = FrontierIntelligenceBridge(commit_sha="test_commit_sha_555")
    with pytest.raises(ValueError, match="has unsafe score"):
        bridge.adapt_and_dispatch(proposal, authorized_map)


def test_provenance_hash_determinism():
    h1 = compute_bridge_provenance_hash("sel_1", "front_1", ("c1", "c2"), "sha_123")
    h2 = compute_bridge_provenance_hash("sel_1", "front_1", ("c1", "c2"), "sha_123")
    h3 = compute_bridge_provenance_hash("sel_1", "front_1", ("c1", "c2"), "sha_456")

    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64
