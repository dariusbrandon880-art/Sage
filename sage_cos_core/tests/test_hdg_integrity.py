"""SAGE SPEK HDG v2 Epistemic Causality Integrity Tests."""

import json
import pytest
from pathlib import Path

from sage_cos_core.sage.core.models import Proposal, HypothesisNode
from sage_cos_core.sage.core.hdg import HDGEngine
from sage_cos_core.sage.core.spek import SAGEPolicyEnforcementKernel


@pytest.fixture
def clean_spek(tmp_path):
    """Fixture that initializes a clean SPEK workspace under a temporary path."""
    config_dir = tmp_path / "sage_cos_core/.sage/config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_data = {
        "spek_version": "1.1.0",
        "evidence_threshold": 0.8,
        "csi_threshold": 0.9,
        "attestation_provider": "local_deterministic",
        "runtime_mode": "enforcement"
    }
    with open(config_dir / "runtime.json", "w") as f:
        json.dump(config_data, f)

    spek = SAGEPolicyEnforcementKernel(root_dir=tmp_path)
    return spek


def test_contradiction_detection(clean_spek):
    """Test 3: Contradiction detection.

    Expected: REJECTED, HDG preserved.
    """
    # Create first node establishing claim A
    p1 = Proposal("p_claim_a", "Claim A Rule", {"rule_body": "Allow CORS"})
    clean_spek.submit_proposal(p1, [], 0.95, metadata={"claim": "Allow CORS from all"})

    assert p1.lifecycle_state == "APPROVED"

    # Submit second proposal claiming "not Allow CORS from all"
    p2 = Proposal("p_claim_not_a", "Contradictory claim A", {"rule_body": "Deny CORS"})
    approved, receipt = clean_spek.submit_proposal(
        proposal=p2,
        parent_ids=[],
        validation_score=0.95,
        metadata={"claim": "not Allow CORS from all"}
    )

    assert not approved
    assert receipt.lifecycle_state == "REJECTED"
    assert p2.lifecycle_state == "REJECTED"

    # Verify contradiction marker was created in HDG node
    hdg_node = clean_spek.hdg.get_node(f"node_{p2.proposal_id}")
    assert hdg_node is not None
    assert any("Contradiction:" in marker for marker in hdg_node.contradiction_markers)


def test_hdg_ancestry_preservation(clean_spek):
    """Test that complete hypothesis node parent ancestry list is preserved and missing parents fail closed."""
    p1 = Proposal("p_root", "Root", {"body": "Root Rule"})
    clean_spek.submit_proposal(p1, [], 0.9)

    p2 = Proposal("p_child", "Child", {"body": "Child Rule"})
    clean_spek.submit_proposal(p2, [f"node_{p1.proposal_id}"], 0.9)

    p3 = Proposal("p_grandchild", "Grandchild", {"body": "Grandchild Rule"})
    clean_spek.submit_proposal(p3, [f"node_{p2.proposal_id}"], 0.9)

    # Grandchild should have root and child in its complete ancestry chain
    ancestry = clean_spek.hdg.get_ancestry(f"node_{p3.proposal_id}")
    assert f"node_{p2.proposal_id}" in ancestry
    assert f"node_{p1.proposal_id}" in ancestry

    # Attempting to submit a proposal with a non-existent parent must raise ValueError and fail closed
    p_broken = Proposal("p_broken", "Broken Rule", {"body": "Broken"})
    with pytest.raises(ValueError, match="Ancestry Broken: Parent hypothesis node"):
        clean_spek.submit_proposal(p_broken, ["node_nonexistent_parent_id"], 0.9)


def test_hdg_corruption_detection(clean_spek):
    """Test 4: HDG corruption detection.

    Expected: system halts safely (raises critical load/integrity exceptions).
    """
    # Write a valid graph first
    p1 = Proposal("p_001", "P1", {"data": 1})
    clean_spek.submit_proposal(p1, [], 0.9)

    # Tamper with the hdg_causality.json file by injecting corrupted invalid JSON
    hdg_path = clean_spek.hdg.storage_path
    with open(hdg_path, "w") as f:
        f.write("{ invalid corrupted json state ... }")

    # Re-instantiating the HDG engine must fail-closed with an exception immediately
    with pytest.raises(RuntimeError, match="CRITICAL INTEGRITY FAILURE: HDG state is corrupted"):
        HDGEngine(storage_path=hdg_path)
