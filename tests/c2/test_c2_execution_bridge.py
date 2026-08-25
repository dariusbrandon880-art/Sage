"""Tests for Governed C2 Execution Bridge."""

import pytest
from sage.c2.c2_execution_bridge import (
    C2ExecutionBridge,
    C2ExecutionRequest,
    C2ExecutionReceipt,
)


def test_execution_receipt_hash_integrity():
    receipt = C2ExecutionReceipt(
        receipt_id="rcpt-001",
        request_id="req-001",
        command="READ",
        target_path="sage/c2/test.py",
        starting_head_sha="b44b892",
        resulting_head_sha="b44b892",
        status="SUCCESS",
    )
    receipt.receipt_hash = receipt.compute_hash()
    assert len(receipt.receipt_hash) == 64
    assert receipt.receipt_hash == receipt.compute_hash()


def test_execution_bridge_invalid_command():
    bridge = C2ExecutionBridge(current_head_sha="b44b892")
    req = C2ExecutionRequest(
        request_id="req-invalid",
        command="EXPLODE",
        target_path="sage/experimental/airspace",
        expected_head_sha="b44b892",
    )
    receipt = bridge.execute(req)
    assert receipt.status == "REJECTED"
    assert "Invalid command" in receipt.error_message


def test_execution_bridge_head_sha_drift():
    bridge = C2ExecutionBridge(current_head_sha="b44b892")
    req = C2ExecutionRequest(
        request_id="req-drift",
        command="READ",
        target_path="sage/experimental/airspace",
        expected_head_sha="stale_sha_123",
    )
    receipt = bridge.execute(req)
    assert receipt.status == "REJECTED"
    assert "HEAD SHA drift mismatch" in receipt.error_message


def test_execution_bridge_protected_namespace_rejects_without_auth():
    bridge = C2ExecutionBridge(current_head_sha="b44b892")
    req = C2ExecutionRequest(
        request_id="req-prot",
        command="WRITE",
        target_path="sage/core/spek.py",
        expected_head_sha="b44b892",
    )
    receipt = bridge.execute(req)
    assert receipt.status == "REJECTED"
    assert "Unauthorized mutation attempt" in receipt.error_message


def test_execution_bridge_protected_namespace_permits_with_auth():
    bridge = C2ExecutionBridge(current_head_sha="b44b892")
    req = C2ExecutionRequest(
        request_id="req-prot-auth",
        command="WRITE",
        target_path="sage/core/spek.py",
        expected_head_sha="b44b892",
        auth_token="SAGE_SYSTEM_AUTH_TOKEN",
    )
    receipt = bridge.execute(req)
    assert receipt.status == "SUCCESS"


def test_execution_bridge_commit_advances_head():
    bridge = C2ExecutionBridge(current_head_sha="b44b892")
    req = C2ExecutionRequest(
        request_id="req-commit",
        command="COMMIT",
        target_path="sage/experimental/test.py",
        expected_head_sha="b44b892",
    )
    receipt = bridge.execute(req)
    assert receipt.status == "SUCCESS"
    assert receipt.starting_head_sha == "b44b892"
    assert receipt.resulting_head_sha != "b44b892"
    assert bridge.current_head_sha == receipt.resulting_head_sha
