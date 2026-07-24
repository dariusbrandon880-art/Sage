"""SAGE SPEK Core Orchestration and Integration Tests."""

import concurrent.futures
import json
import pytest
from pathlib import Path

from sage_cos_core.sage.core.models import Proposal
from sage_cos_core.sage.core.spek import SAGEPolicyEnforcementKernel


@pytest.fixture
def clean_spek(tmp_path):
    """Fixture that initializes a clean SPEK workspace under a temporary path."""
    # Create configuration folder and config file in tmp_path
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

    # Initialize SPEK
    spek = SAGEPolicyEnforcementKernel(root_dir=tmp_path)
    return spek


def test_valid_proposal_approval(clean_spek):
    """Test 1: Valid proposal approval.

    Expected: execution_permission=True, state=APPROVED, promotion queue updated.
    """
    proposal = Proposal(
        proposal_id="p_valid_001",
        title="Valid Control Standard Rule",
        content={"rule_definition": "Enforce TLS v1.3 only"},
        evidence_references=["ev_tls_check_ok_001"]
    )

    # Root node has no parent_ids
    approved, receipt = clean_spek.submit_proposal(
        proposal=proposal,
        parent_ids=[],
        validation_score=0.9,  # >= 0.8 threshold
        metadata={"claim": "TLS validation successful"}
    )

    assert approved
    assert receipt.execution_permission is True
    assert receipt.lifecycle_state == "APPROVED"
    assert proposal.lifecycle_state == "APPROVED"

    # Confirm promotion_queue.log contains the log entry
    queue_path = clean_spek.compliance.promotion_queue_path
    assert queue_path.exists()
    with open(queue_path, "r") as f:
        lines = f.readlines()
        assert len(lines) == 1
        log_entry = json.loads(lines[0])
        assert log_entry["proposal_id"] == "p_valid_001"
        assert log_entry["lifecycle_state"] == "PROMOTION_QUEUE"


def test_low_evidence_rejection(clean_spek):
    """Test 2: Low evidence rejection.

    Expected: execution_permission=False, state=REJECTED, negative_results updated.
    """
    proposal = Proposal(
        proposal_id="p_weak_002",
        title="Weak Evidence Control Rule",
        content={"rule_definition": "Enforce MD5 hash checks"},
        evidence_references=["ev_md5_unverified"]
    )

    approved, receipt = clean_spek.submit_proposal(
        proposal=proposal,
        parent_ids=[],
        validation_score=0.4,  # < 0.8 threshold
        metadata={"claim": "MD5 validation unverified"}
    )

    assert not approved
    assert receipt.execution_permission is False
    assert receipt.lifecycle_state == "REJECTED"
    assert proposal.lifecycle_state == "REJECTED"

    # Confirm negative_results.json contains the rejection entry
    neg_path = clean_spek.compliance.negative_results_path
    assert neg_path.exists()
    with open(neg_path, "r") as f:
        data = json.load(f)
        assert "p_weak_002" in data
        assert any("Insufficient validation score" in r for r in data["p_weak_002"]["rejection_reasons"])


def test_audit_tampering_detection(clean_spek):
    """Test 5: Audit tampering detection.

    Expected: receipt chain failure detected.
    """
    # Create two valid proposals to form a chain
    p1 = Proposal("p_001", "P1", {"data": 1})
    p2 = Proposal("p_002", "P2", {"data": 2})

    clean_spek.submit_proposal(p1, [], 0.95)
    clean_spek.submit_proposal(p2, [f"node_{p1.proposal_id}"], 0.95)

    # Vault is verified as correct
    assert clean_spek.verify_vault_integrity() is True

    # Tamper with the first receipt's lifecycle state in vault file
    vault_path = clean_spek.compliance.spek_vault_path
    with open(vault_path, "r") as f:
        vault_data = json.load(f)

    # Mutate receipt
    vault_data[0]["lifecycle_state"] = "APPROVED_BY_TAMPERER"

    with open(vault_path, "w") as f:
        json.dump(vault_data, f)

    # Re-initialize SPEK Compliance to force load & verify
    with pytest.raises(RuntimeError, match="SPEK receipt vault chain integrity is compromised"):
        clean_spek.compliance.load_receipt_vault()


def test_concurrent_transaction_safety(clean_spek):
    """Test 7: Concurrent transaction safety.

    Expected: no audit corruption.
    """
    import uuid

    def submit_worker(idx):
        proposal = Proposal(
            proposal_id=f"p_concurrent_{idx}_{uuid.uuid4().hex[:4]}",
            title=f"Concurrent Proposal {idx}",
            content={"val": idx}
        )
        try:
            approved, receipt = clean_spek.submit_proposal(proposal, [], 0.9)
            return True
        except Exception:
            return False

    # Execute 30 rapid state mutations concurrently using thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(submit_worker, i) for i in range(30)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(results)
    assert len(clean_spek.compliance.receipts) == 30
    assert clean_spek.verify_vault_integrity() is True
