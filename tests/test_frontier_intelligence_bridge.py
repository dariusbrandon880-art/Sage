import pytest

from sage.c2.frontier_intelligence_bridge import FrontierIntelligenceBridge, FrontierBridgeDispatchReceipt
from sage.experimental.sagi_discovery_flight_selector import (
    DiscoveryCandidate,
    FlightRole,
    SAGIDiscoveryFlightSelector,
)


@pytest.fixture
def sample_proposal():
    selector = SAGIDiscoveryFlightSelector()
    frontier_digest = "digest_frontier_001_test"
    candidates = (
        DiscoveryCandidate(
            candidate_id="cand_a",
            description="SAGI Research Provenance",
            role=FlightRole.CONSEQUENT_FRONTIER,
            consequentiality=0.9,
            information_gain=0.8,
            falsification_value=0.7,
            safety=0.95,
            evidence_gap=0.5,
            provenance_ref="ref_sagi_001",
        ),
        DiscoveryCandidate(
            candidate_id="cand_b",
            description="Runtime Context Rehydration",
            role=FlightRole.INFORMATION_GAIN,
            consequentiality=0.8,
            information_gain=0.9,
            falsification_value=0.6,
            safety=0.9,
            evidence_gap=0.4,
            provenance_ref="ref_runtime_001",
        ),
        DiscoveryCandidate(
            candidate_id="cand_c",
            description="Flight Harness Substrate",
            role=FlightRole.FALSIFICATION,
            consequentiality=0.7,
            information_gain=0.7,
            falsification_value=0.9,
            safety=0.85,
            evidence_gap=0.6,
            provenance_ref="ref_harness_001",
        ),
        DiscoveryCandidate(
            candidate_id="cand_d",
            description="Architecture Guard Audit",
            role=FlightRole.RECOVERY_REGRESSION,
            consequentiality=0.85,
            information_gain=0.6,
            falsification_value=0.8,
            safety=0.95,
            evidence_gap=0.3,
            provenance_ref="ref_act_001",
        ),
        DiscoveryCandidate(
            candidate_id="cand_e",
            description="Capability Warehouse Check",
            role=FlightRole.INDEPENDENT_TRANSFER,
            consequentiality=0.6,
            information_gain=0.8,
            falsification_value=0.5,
            safety=0.9,
            evidence_gap=0.7,
            provenance_ref="ref_archive_001",
        ),
    )
    return selector.select(candidates, frontier_digest=frontier_digest)


def test_bridge_dispatches_when_all_candidates_authorized(sample_proposal):
    bridge = FrontierIntelligenceBridge()
    authorized_ids = ("cand_a", "cand_b", "cand_c", "cand_d", "cand_e")
    commit_sha = "2f29952931f7937d15711092da3faf1e28764135"

    receipt = bridge.bridge_and_dispatch(
        sample_proposal,
        authorized_candidate_ids=authorized_ids,
        commit_sha=commit_sha,
    )

    assert receipt.is_authorized is True
    assert len(receipt.unauthorized_candidate_ids) == 0
    assert len(receipt.authorized_candidate_ids) == 5
    assert receipt.dispatch_result is not None
    assert receipt.dispatch_result.wave_verdict == "PASS"
    assert len(receipt.bridge_digest) == 64


def test_bridge_fails_closed_when_any_candidate_unauthorized(sample_proposal):
    bridge = FrontierIntelligenceBridge()
    # Missing cand_e
    authorized_ids = ("cand_a", "cand_b", "cand_c", "cand_d")
    commit_sha = "2f29952931f7937d15711092da3faf1e28764135"

    receipt = bridge.bridge_and_dispatch(
        sample_proposal,
        authorized_candidate_ids=authorized_ids,
        commit_sha=commit_sha,
    )

    assert receipt.is_authorized is False
    assert receipt.unauthorized_candidate_ids == ("cand_e",)
    assert len(receipt.authorized_candidate_ids) == 4
    assert receipt.dispatch_result is None
    assert len(receipt.bridge_digest) == 64
