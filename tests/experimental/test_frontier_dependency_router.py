"""Unit tests for Frontier Dependency Router and adversarial validation."""

import pytest
from sage.experimental.frontier_dependency_router import (
    FrontierDependencyRouter,
    CandidateDependencyGraph,
    CandidateSecurityTier,
)


def test_frontier_dependency_router_normal_routing():
    """Verify normal candidate routing through dependency and boundary analysis."""
    router = FrontierDependencyRouter()
    graph = CandidateDependencyGraph(
        candidate_id="cand_test_001",
        nodes=("node_a", "node_b"),
        edges=(("node_a", "node_b"),),
        imports=("sage.experimental.act",),
    )

    proposal = router.route_candidate(
        candidate_id="cand_test_001",
        dependency_graph=graph,
        target_file_paths=("sage/experimental/act/test.py",),
        provenance_ref="ref_prov_12345",
    )

    assert proposal.candidate_id == "cand_test_001"
    assert proposal.authorized is False  # Fail-closed default
    assert proposal.requires_human_approval is True
    assert proposal.authoritative is False
    assert proposal.security_tier == CandidateSecurityTier.EXPERIMENTAL
    assert proposal.proposal_digest is not None


def test_frontier_dependency_router_protected_path_detection():
    """Verify routing assigns PROTECTED_CORE tier when target files touch core paths."""
    router = FrontierDependencyRouter()
    graph = CandidateDependencyGraph(
        candidate_id="cand_test_protected",
        nodes=("node_a",),
        edges=(),
        imports=("sage.runtime",),
    )

    proposal = router.route_candidate(
        candidate_id="cand_test_protected",
        dependency_graph=graph,
        target_file_paths=("sage/runtime/engine.py",),
        provenance_ref="ref_prov_protected",
    )

    assert proposal.security_tier == CandidateSecurityTier.PROTECTED_CORE
    assert proposal.affected_namespaces[0].is_protected_core is True
    assert proposal.affected_namespaces[0].requires_explicit_override is True


def test_adversarial_rejection_missing_id_and_provenance():
    """Verify rejection of empty candidate ID or provenance reference."""
    router = FrontierDependencyRouter()
    graph = CandidateDependencyGraph(
        candidate_id="cand_001",
        nodes=("node_a",),
        edges=(),
        imports=(),
    )

    with pytest.raises(ValueError, match="Candidate ID cannot be empty"):
        router.route_candidate("", graph, ("sage/experimental/a.py",), "ref_123")

    with pytest.raises(ValueError, match="Provenance reference is required"):
        router.route_candidate("cand_001", graph, ("sage/experimental/a.py",), "")


def test_adversarial_rejection_empty_graph():
    """Verify rejection of empty dependency graph."""
    router = FrontierDependencyRouter()
    graph = CandidateDependencyGraph(
        candidate_id="cand_empty",
        nodes=(),
        edges=(),
        imports=(),
    )

    with pytest.raises(ValueError, match="Dependency graph cannot be empty"):
        router.route_candidate("cand_empty", graph, ("sage/experimental/a.py",), "ref_123")


def test_adversarial_rejection_invalid_provenance_format():
    """Verify rejection of invalid provenance reference format."""
    router = FrontierDependencyRouter()
    graph = CandidateDependencyGraph(
        candidate_id="cand_invalid_prov",
        nodes=("node_a",),
        edges=(),
        imports=(),
    )

    with pytest.raises(ValueError, match="Invalid provenance reference format"):
        router.route_candidate("cand_invalid_prov", graph, ("sage/experimental/a.py",), "untrusted_prov_123")


def test_adversarial_rejection_forged_signature():
    """Verify rejection of forged or invalid authorization signatures."""
    router = FrontierDependencyRouter()
    graph = CandidateDependencyGraph(
        candidate_id="cand_sig",
        nodes=("node_a",),
        edges=(),
        imports=(),
    )

    with pytest.raises(ValueError, match="Invalid or forged authorization signature"):
        router.route_candidate(
            "cand_sig",
            graph,
            ("sage/experimental/a.py",),
            "ref_prov_123",
            signature="forged_signature_bypass",
        )


def test_capture_learning_loop_feedback():
    """Verify capturing C2 learning feedback on proposal."""
    router = FrontierDependencyRouter()
    graph = CandidateDependencyGraph(
        candidate_id="cand_feedback",
        nodes=("node_a",),
        edges=(),
        imports=(),
    )

    proposal = router.route_candidate(
        candidate_id="cand_feedback",
        dependency_graph=graph,
        target_file_paths=("sage/experimental/a.py",),
        provenance_ref="ref_prov_fb",
    )

    feedback = router.capture_feedback(
        proposal,
        blocked_modes=("forged_signature", "missing_provenance"),
        candidate_frontiers=("intake_router_expansion",),
        timestamp_utc="2026-08-23T23:50:00Z",
    )

    assert feedback.proposal_digest == proposal.proposal_digest
    assert len(feedback.blocked_failure_modes) == 2
    assert "forged_signature" in feedback.blocked_failure_modes
