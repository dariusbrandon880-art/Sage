"""Adversarial Validation Test Suite for SAGE SPEK v1.1."""

import json
import threading
import pytest
from pathlib import Path

from sage.core import (
    BoundaryEnforcer,
    CryptographicAttestationProvider,
    HDGEngine,
    ComplianceEngine,
    SpekEngine,
    RuleState,
    Proposal,
    HypothesisNode,
)


@pytest.fixture
def temp_spek_paths(tmp_path):
    """Fixture providing isolated temporary paths for SPEK files."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    config_path = config_dir / "runtime.json"

    # Write a default test config
    config_data = {
        "spek_version": "1.1",
        "evidence_threshold": 0.7,
        "csi_threshold": 0.5,
        "attestation_provider": "Mock",
        "runtime_mode": "testing",
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f)

    audit_dir = tmp_path / "validation" / "audit"
    audit_dir.mkdir(parents=True)

    vault_path = audit_dir / "spek_vault.json"
    promotion_path = audit_dir / "promotion_queue.log"
    rejection_path = audit_dir / "negative_results.json"
    hdg_path = audit_dir / "hdg_causality.json"

    # Initialize ledgers
    with open(vault_path, "w") as f:
        json.dump([], f)
    with open(rejection_path, "w") as f:
        json.dump([], f)
    with open(hdg_path, "w") as f:
        json.dump([], f)
    promotion_path.touch()

    return {
        "config_path": config_path,
        "vault_path": vault_path,
        "promotion_path": promotion_path,
        "rejection_path": rejection_path,
        "hdg_path": hdg_path,
    }


def test_valid_proposal_approval(temp_spek_paths):
    """Test that a valid proposal transitions to APPROVED, logs promotion, and signs receipts."""
    engine = SpekEngine(
        config_path=temp_spek_paths["config_path"],
        vault_path=temp_spek_paths["vault_path"],
        promotion_path=temp_spek_paths["promotion_path"],
        rejection_path=temp_spek_paths["rejection_path"],
        hdg_path=temp_spek_paths["hdg_path"],
    )

    token = BoundaryEnforcer.SYSTEM_TOKEN

    proposal = engine.process_proposal(
        proposal_id="rule_001",
        description="Verify database replication topology",
        category="infrastructure",
        author="jules",
        parent_ids=[],
        evidence_refs=["ref_db_001", "ref_db_002"],
        validation_score=0.85,  # Above 0.7 threshold
        auth_token=token,
    )

    # 1. State check
    assert proposal.state == RuleState.APPROVED

    # 2. Promotion queue log check
    with open(temp_spek_paths["promotion_path"], "r") as f:
        log_content = f.read()
    assert "PROMOTED RULE" in log_content
    assert "proposal_id=rule_001" in log_content

    # 3. Dynamic ledger audits & receipts check
    with open(temp_spek_paths["vault_path"], "r") as f:
        vault_data = json.load(f)

    # Should have 4 state transition receipts: PROPOSED, EVALUATED, VALIDATED, APPROVED
    assert len(vault_data) == 4
    assert vault_data[0]["lifecycle_state"] == "PROPOSED"
    assert vault_data[1]["lifecycle_state"] == "EVALUATED"
    assert vault_data[2]["lifecycle_state"] == "VALIDATED"
    assert vault_data[3]["lifecycle_state"] == "APPROVED"

    # Verify chain hashes and signatures
    assert engine.compliance.verify_vault_integrity(engine.attestation) is True


def test_low_evidence_rejection(temp_spek_paths):
    """Test that a proposal with low evidence transitions to REJECTED and logs to negative_results."""
    engine = SpekEngine(
        config_path=temp_spek_paths["config_path"],
        vault_path=temp_spek_paths["vault_path"],
        promotion_path=temp_spek_paths["promotion_path"],
        rejection_path=temp_spek_paths["rejection_path"],
        hdg_path=temp_spek_paths["hdg_path"],
    )

    token = BoundaryEnforcer.SYSTEM_TOKEN

    proposal = engine.process_proposal(
        proposal_id="rule_002",
        description="Experimental routing algorithm",
        category="networking",
        author="developer_bob",
        parent_ids=[],
        evidence_refs=["ref_exp_01"],
        validation_score=0.55,  # Below 0.7 threshold
        auth_token=token,
    )

    # 1. State check
    assert proposal.state == RuleState.REJECTED

    # 2. Rejection file check
    with open(temp_spek_paths["rejection_path"], "r") as f:
        rejections = json.load(f)
    assert len(rejections) == 1
    assert rejections[0]["proposal_id"] == "rule_002"
    assert rejections[0]["status"] == "REJECTED"
    assert "below evidence threshold" in rejections[0]["reason"]

    # 3. Promotion queue must NOT contain it
    with open(temp_spek_paths["promotion_path"], "r") as f:
        log_content = f.read()
    assert "proposal_id=rule_002" not in log_content

    # 4. Vault must contain REJECTED receipt
    with open(temp_spek_paths["vault_path"], "r") as f:
        vault_data = json.load(f)
    assert len(vault_data) == 4  # PROPOSED -> EVALUATED -> VALIDATED -> REJECTED
    assert vault_data[-1]["lifecycle_state"] == "REJECTED"
    assert vault_data[-1]["execution_permission"] is False

    # Vault integrity check
    assert engine.compliance.verify_vault_integrity(engine.attestation) is True


def test_contradiction_detection(temp_spek_paths):
    """Test that contradiction detection blocks execution and preserves HDG lineage."""
    engine = SpekEngine(
        config_path=temp_spek_paths["config_path"],
        vault_path=temp_spek_paths["vault_path"],
        promotion_path=temp_spek_paths["promotion_path"],
        rejection_path=temp_spek_paths["rejection_path"],
        hdg_path=temp_spek_paths["hdg_path"],
    )

    token = BoundaryEnforcer.SYSTEM_TOKEN

    # 1. Propose node A
    engine.process_proposal(
        proposal_id="node_a",
        description="DB replica has read consistency",
        category="database",
        author="jules",
        parent_ids=[],
        evidence_refs=["ref_db_001"],
        validation_score=0.9,
        auth_token=token,
    )

    # 2. Propose node B which contradicts ancestor node A
    with pytest.raises(ValueError, match="SPEK Execution Blocked: Contradiction detected"):
        engine.process_proposal(
            proposal_id="node_b",
            description="DB replica has eventual consistency only",
            category="database",
            author="jules",
            parent_ids=["node_a"],  # A is ancestor/parent
            evidence_refs=["ref_db_002"],
            validation_score=0.9,
            contradictions=["node_a"],  # Contradicts ancestor!
            auth_token=token,
        )

    # Verify HDG node was added/preserved despite blocking
    assert "node_b" in engine.hdg.nodes
    node_b = engine.hdg.nodes["node_b"]
    assert node_b.is_promoted is False


def test_hdg_corruption_detection(temp_spek_paths):
    """Test that HDGEngine fails closed on corrupted state, and cycle detection blocks execution."""
    token = BoundaryEnforcer.SYSTEM_TOKEN

    # Part A: Fail closed on malformed disk storage
    with open(temp_spek_paths["hdg_path"], "w") as f:
        f.write("{invalid_json_data]")

    with pytest.raises(ValueError, match="HDG Epistemic Causality Engine Failed Closed"):
        HDGEngine(storage_path=temp_spek_paths["hdg_path"])

    # Reset path
    with open(temp_spek_paths["hdg_path"], "w") as f:
        json.dump([], f)

    # Part B: Fail closed on cyclical references
    hdg = HDGEngine(storage_path=temp_spek_paths["hdg_path"])

    node_1 = HypothesisNode(node_id="node_1", description="First node", parent_ids=[])
    hdg.add_node(node_1, token)

    node_2 = HypothesisNode(node_id="node_2", description="Second node", parent_ids=["node_1"])
    hdg.add_node(node_2, token)

    # Injecting cycle: node_1 parent becomes node_2
    node_1_cycle = HypothesisNode(node_id="node_1", description="First node", parent_ids=["node_2"])

    with pytest.raises(ValueError, match="Circular dependency cycle detected"):
        hdg.add_node(node_1_cycle, token)


def test_audit_tampering_detection(temp_spek_paths):
    """Test that tampering with the append-only ledger is detected during verification."""
    engine = SpekEngine(
        config_path=temp_spek_paths["config_path"],
        vault_path=temp_spek_paths["vault_path"],
        promotion_path=temp_spek_paths["promotion_path"],
        rejection_path=temp_spek_paths["rejection_path"],
        hdg_path=temp_spek_paths["hdg_path"],
    )

    token = BoundaryEnforcer.SYSTEM_TOKEN

    # Propose rule to fill the ledger
    engine.process_proposal(
        proposal_id="rule_005",
        description="Database audit rule",
        category="security",
        author="jules",
        parent_ids=[],
        evidence_refs=["ref_sec_01"],
        validation_score=0.95,
        auth_token=token,
    )

    assert engine.compliance.verify_vault_integrity(engine.attestation) is True

    # Tamper with the ledger file directly (using the valid token to permit bypass of boundary)
    with open(temp_spek_paths["vault_path"], "r") as f:
        vault_data = json.load(f)

    # Tamper with the first receipt's state
    vault_data[0]["lifecycle_state"] = "APPROVED"

    with open(temp_spek_paths["vault_path"], "w") as f:
        json.dump(vault_data, f)

    # Re-evaluate, should fail verification
    assert engine.compliance.verify_vault_integrity(engine.attestation) is False


def test_protected_path_mutation_attempt(temp_spek_paths):
    """Test that unauthorized modifications to critical areas are blocked by BoundaryEnforcer."""
    enforcer = BoundaryEnforcer()

    # Attempt to write to critical path without valid token
    with pytest.raises(PermissionError, match="Security Boundary Enforcement Violation"):
        enforcer.validate_mutation(".sage/validation/audit/spek_vault.json", auth_token="unauthorized_token")

    # Attempt to write with correct token succeeds
    enforcer.validate_mutation(".sage/validation/audit/spek_vault.json", auth_token=BoundaryEnforcer.SYSTEM_TOKEN)

    # Test that non-protected path is bypassed
    enforcer.validate_mutation("unprotected_folder/logs.txt", auth_token="bad_token")


def test_concurrent_transaction_safety(temp_spek_paths):
    """Test that concurrent rule proposal threads write safely without corrupting the audit ledger."""
    engine = SpekEngine(
        config_path=temp_spek_paths["config_path"],
        vault_path=temp_spek_paths["vault_path"],
        promotion_path=temp_spek_paths["promotion_path"],
        rejection_path=temp_spek_paths["rejection_path"],
        hdg_path=temp_spek_paths["hdg_path"],
    )

    token = BoundaryEnforcer.SYSTEM_TOKEN

    num_threads = 5
    threads = []
    errors = []

    def worker(worker_id):
        try:
            engine.process_proposal(
                proposal_id=f"concurrent_rule_{worker_id}",
                description=f"Thread safe worker rule {worker_id}",
                category="concurrency_test",
                author=f"worker_{worker_id}",
                parent_ids=[],
                evidence_refs=[f"ref_worker_{worker_id}"],
                validation_score=0.8,
                auth_token=token,
            )
        except Exception as e:
            errors.append(e)

    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # No execution errors should occur
    assert len(errors) == 0

    # Load vault, should have 4 receipts per thread = 20 receipts
    with open(temp_spek_paths["vault_path"], "r") as f:
        vault_data = json.load(f)

    assert len(vault_data) == num_threads * 4

    # Verify vault integrity holds up completely
    assert engine.compliance.verify_vault_integrity(engine.attestation) is True
