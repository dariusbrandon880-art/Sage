"""Tests for the bounded SAGI ResearchGraph -> C2 frontier seam."""

import pytest

from sage.c2.sagi_frontier_bridge import SAGIFrontierBridge
from sage.experimental.sagi.research_graph import SAGIResearchNode


ANCHOR = "sage-identity-anchor"


def make_node(**overrides):
    values = {
        "node_id": "node_cycle_1_1",
        "cycle_id": "cycle_1",
        "identity_anchor": ANCHOR,
        "candidate_signature": "a" * 64,
        "guardian_result": "APPROVED",
        "measurement_summary": {"tested": 1, "approved": 1, "rejected": 0},
    }
    values.update(overrides)
    return SAGIResearchNode(**values)


def test_research_graph_node_becomes_bounded_c2_candidate():
    node = make_node()
    proposal = SAGIFrontierBridge(ANCHOR).to_frontier_candidate(
        node,
        target="sage/c2/frontier_admission.py",
        base_sha="980f79a89a4dfdaf3979756d78251846eeca2d18",
        collision_zone="sage/c2/frontier_admission.py",
        evidence_required=["sagi://research-graph/node_cycle_1_1"],
        stop_condition="C2 verification passes",
    )

    assert proposal.candidate.frontier_id == "sagi-node_cycle_1_1"
    assert proposal.candidate.state.value == "UNSTARTED"
    assert proposal.research_node_id == node.node_id
    assert proposal.research_node_sha256 == node.node_sha256
    assert proposal.identity_anchor == ANCHOR
    assert node.node_sha256 in proposal.candidate.source


def test_unapproved_research_node_fails_closed():
    node = make_node(guardian_result="REJECTED")
    with pytest.raises(ValueError, match="not approved"):
        SAGIFrontierBridge(ANCHOR).to_frontier_candidate(
            node,
            target="target.py",
            base_sha="980f79a89a4dfdaf3979756d78251846eeca2d18",
            collision_zone="target.py",
            stop_condition="pass",
        )


def test_identity_mismatch_fails_closed():
    node = make_node(identity_anchor="different-anchor")
    with pytest.raises(ValueError, match="identity anchor"):
        SAGIFrontierBridge(ANCHOR).to_frontier_candidate(
            node,
            target="target.py",
            base_sha="980f79a89a4dfdaf3979756d78251846eeca2d18",
            collision_zone="target.py",
            stop_condition="pass",
        )


def test_tampered_research_node_fails_closed():
    node = make_node()
    node.candidate_signature = "b" * 64
    with pytest.raises(ValueError, match="integrity"):
        SAGIFrontierBridge(ANCHOR).to_frontier_candidate(
            node,
            target="target.py",
            base_sha="980f79a89a4dfdaf3979756d78251846eeca2d18",
            collision_zone="target.py",
            stop_condition="pass",
        )
