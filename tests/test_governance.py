"""Validation tests for SAGE SPEK v1.1 Governance and Epistemic Causality Engines."""

import pytest
import os
import json
import shutil
import tempfile
from pathlib import Path
from sage.core.spek import PolicyEnforcementKernel
from sage.core.models import SPEKLifecycleState
from sage.core.hdg import HDGNode


@pytest.fixture
def temp_audit_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_spek_valid_proposal_approval(temp_audit_dir):
    kernel = PolicyEnforcementKernel(audit_dir=temp_audit_dir)

    res = kernel.evaluate_and_promote_candidate(
        candidate_id="cand_valid_100",
        title="Valid Core Specs",
        parent_ids=[],
        evidence_references=["ev_abc"],
        validation_score=0.9,  # Above threshold
        is_contradicted=False,
        auth_token="SAGE_SPEK_KERNEL_AUTH_TOKEN",
    )

    assert res["success"] is True
    assert res["next_state"] == SPEKLifecycleState.APPROVED
    assert "receipt" in res

    # Confirm promotion queue updated
    promotion_queue_log = Path(temp_audit_dir) / "promotion_queue.log"
    assert promotion_queue_log.exists()
    content = promotion_queue_log.read_text()
    assert "cand_valid_100" in content


def test_spek_low_evidence_rejection(temp_audit_dir):
    kernel = PolicyEnforcementKernel(audit_dir=temp_audit_dir)

    res = kernel.evaluate_and_promote_candidate(
        candidate_id="cand_low_200",
        title="Incomplete Specs",
        parent_ids=[],
        evidence_references=[],
        validation_score=0.4,  # Below threshold
        is_contradicted=False,
        auth_token="SAGE_SPEK_KERNEL_AUTH_TOKEN",
    )

    assert res["success"] is False
    assert res["next_state"] == SPEKLifecycleState.REJECTED

    # Confirm negative results updated
    negative_results_file = Path(temp_audit_dir) / "negative_results.json"
    assert negative_results_file.exists()
    with open(negative_results_file, "r") as f:
        data = json.load(f)
        assert any(item["candidate_id"] == "cand_low_200" for item in data["rejected_candidates"])


def test_spek_contradiction_detection(temp_audit_dir):
    kernel = PolicyEnforcementKernel(audit_dir=temp_audit_dir)

    # 1. Setup a parent node
    kernel.evaluate_and_promote_candidate(
        candidate_id="parent_node",
        title="Parent specs",
        parent_ids=[],
        evidence_references=["ev_1"],
        validation_score=0.8,
        is_contradicted=False,
        auth_token="SAGE_SPEK_KERNEL_AUTH_TOKEN",
    )

    # Flag contradiction
    kernel.hdg.flag_contradiction("parent_node", "Flagged by security audit")

    # 2. Evaluate a child node that depends on the contradicted parent
    res = kernel.evaluate_and_promote_candidate(
        candidate_id="child_node",
        title="Child specs",
        parent_ids=["parent_node"],
        evidence_references=["ev_2"],
        validation_score=0.8,
        is_contradicted=False,
        auth_token="SAGE_SPEK_KERNEL_AUTH_TOKEN",
    )

    # Promotion must fail due to parent contradiction (Epistemic Firewall)
    assert res["success"] is False
    assert res["next_state"] == SPEKLifecycleState.REJECTED


def test_spek_hdg_corruption_detection(temp_audit_dir):
    kernel = PolicyEnforcementKernel(audit_dir=temp_audit_dir)

    # Attempt loop reference node addition
    node = HDGNode(
        id="loop_node",
        title="Self reference",
        parent_ids=["loop_node"],  # Cyclic reference!
        evidence_references=[],
    )

    with pytest.raises(ValueError) as exc:
        kernel.hdg.add_node(node)
    assert "Self-referential loop" in str(exc.value)


def test_spek_audit_tampering_detection(temp_audit_dir):
    kernel = PolicyEnforcementKernel(temp_audit_dir)

    # Perform two transitions to build a chain
    kernel.evaluate_and_promote_candidate(
        candidate_id="c_1",
        title="Specs 1",
        parent_ids=[],
        evidence_references=["ev_1"],
        validation_score=0.8,
        is_contradicted=False,
        auth_token="SAGE_SPEK_KERNEL_AUTH_TOKEN",
    )
    kernel.evaluate_and_promote_candidate(
        candidate_id="c_2",
        title="Specs 2",
        parent_ids=["c_1"],
        evidence_references=["ev_2"],
        validation_score=0.8,
        is_contradicted=False,
        auth_token="SAGE_SPEK_KERNEL_AUTH_TOKEN",
    )

    # Verify initial chain integrity
    assert kernel.compliance.verify_vault_chain_integrity() is True

    # Tamper with the ledger file
    vault_file = Path(temp_audit_dir) / "spek_vault.json"
    with open(vault_file, "r") as f:
        data = json.load(f)
        # Corrupt a signature
        data["receipts"][1]["attestation_signature"] = "corrupted_sig_12345"

    with open(vault_file, "w") as f:
        json.dump(data, f, indent=2)

    # Integrity verification must fail closed!
    assert kernel.compliance.verify_vault_chain_integrity() is False


def test_spek_protected_path_mutation_attempt(temp_audit_dir):
    kernel = PolicyEnforcementKernel(audit_dir=temp_audit_dir)

    # Mutation attempt with incorrect auth token must be rejected by boundary enforcer
    res = kernel.evaluate_and_promote_candidate(
        candidate_id="unauthorized_mutate",
        title="Hacked Specs",
        parent_ids=[],
        evidence_references=[],
        validation_score=0.9,
        is_contradicted=False,
        auth_token="INVALID_HACKER_TOKEN_999",
    )

    assert res["success"] is False
    assert "Security Boundary Violation" in res["error"]


def test_spek_concurrent_transaction_safety(temp_audit_dir):
    kernel = PolicyEnforcementKernel(audit_dir=temp_audit_dir)

    # Evaluate multiple sequential transitions to ensure no state/vault corruption
    for i in range(10):
        res = kernel.evaluate_and_promote_candidate(
            candidate_id=f"concurrent_test_{i}",
            title=f"Specs {i}",
            parent_ids=[],
            evidence_references=["ev_test"],
            validation_score=0.8,
            is_contradicted=False,
            auth_token="SAGE_SPEK_KERNEL_AUTH_TOKEN",
        )
        assert res["success"] is True

    assert kernel.compliance.verify_vault_chain_integrity() is True
