"""Tests for the governed C2 execution/provenance simulator."""

import pytest
from sage.c2.c2_execution_bridge import C2ExecutionBridge, C2ExecutionRequest, C2ExecutionReceipt

HEAD = "947408e6e77f9a15fdc2702e32e81b0cd935c733"


def test_receipt_hash_integrity():
    receipt = C2ExecutionReceipt(receipt_id="r", request_id="q", command="READ", target_path="sage/c2/test.py", starting_head_sha=HEAD, resulting_head_sha=HEAD, status="SUCCESS")
    receipt.receipt_hash = receipt.compute_hash()
    assert len(receipt.receipt_hash) == 64
    assert receipt.receipt_hash == receipt.compute_hash()


def test_invalid_command_rejected():
    bridge = C2ExecutionBridge(HEAD)
    receipt = bridge.execute(C2ExecutionRequest(request_id="q", command="EXPLODE", target_path="sage/c2", expected_head_sha=HEAD))
    assert receipt.status == "REJECTED"


def test_head_drift_rejected():
    bridge = C2ExecutionBridge(HEAD)
    receipt = bridge.execute(C2ExecutionRequest(request_id="q", command="READ", target_path="sage/c2", expected_head_sha="stale_sha_123"))
    assert receipt.status == "REJECTED"
    assert "HEAD SHA drift mismatch" in receipt.error_message


def test_protected_namespace_requires_auth():
    bridge = C2ExecutionBridge(HEAD)
    rejected = bridge.execute(C2ExecutionRequest(request_id="q1", command="WRITE", target_path="sage/core/spek.py", expected_head_sha=HEAD))
    assert rejected.status == "REJECTED"
    accepted = bridge.execute(C2ExecutionRequest(request_id="q2", command="WRITE", target_path="sage/core/spek.py", expected_head_sha=HEAD, auth_token="SAGE_SYSTEM_AUTH_TOKEN"))
    assert accepted.status == "SUCCESS"


def test_commit_is_explicitly_simulated():
    bridge = C2ExecutionBridge(HEAD)
    receipt = bridge.execute(C2ExecutionRequest(request_id="q", command="COMMIT", target_path="sage/experimental/test.py", expected_head_sha=HEAD))
    assert receipt.status == "SUCCESS"
    assert receipt.output["simulation"] is True
    assert receipt.resulting_head_sha != HEAD
