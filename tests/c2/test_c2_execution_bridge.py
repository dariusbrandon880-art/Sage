"""Unit and smoke tests for SAGE Governed C2 Execution Bridge v0.1."""
import pytest
from sage.c2.c2_execution_bridge import C2ExecutionBridge, C2ExecutionRequest, C2ExecutionReceipt


def test_execution_receipt_digest():
    """Verify C2ExecutionReceipt computes a valid deterministic SHA-256 digest."""
    receipt = C2ExecutionReceipt(
        execution_id="exec-001",
        actor_id="[SAGE::C2::GPT]",
        action_type="WRITE",
        starting_sha="sha_start_001",
        resulting_sha="sha_result_001",
        files_affected=["sage/experimental/demo.py"],
        result_status="PASS",
    )
    digest = receipt.digest()
    assert isinstance(digest, str)
    assert len(digest) == 64


def test_protected_path_rejection():
    """Verify that requests targeting protected core paths fail closed."""
    bridge = C2ExecutionBridge()
    req = C2ExecutionRequest(
        action_type="WRITE",
        target_path="sage/core/spek.py",
        content="unauthorized edit",
    )
    receipt = bridge.execute_c2_request(req)
    assert receipt.result_status == "REJECTED_PROTECTED_PATH"
    assert "intersects protected core namespace" in receipt.stderr_summary


def test_read_write_diff_execution_flow(tmp_path):
    """Verify governed READ, WRITE, and DIFF operations against a local workspace root."""
    bridge = C2ExecutionBridge(root_dir=tmp_path)

    # 1. Write file
    write_req = C2ExecutionRequest(
        action_type="WRITE",
        target_path="sage/experimental/sample_c2.py",
        content="# Sample C2 write\nprint('c2')",
    )
    write_receipt = bridge.execute_c2_request(write_req)
    assert write_receipt.result_status == "PASS"
    assert "sage/experimental/sample_c2.py" in write_receipt.files_affected

    # 2. Read file
    read_req = C2ExecutionRequest(
        action_type="READ",
        target_path="sage/experimental/sample_c2.py",
    )
    read_receipt = bridge.execute_c2_request(read_req)
    assert read_receipt.result_status == "PASS"
    assert "Read" in read_receipt.stdout_summary

    # 3. Read non-existent file
    read_bad_req = C2ExecutionRequest(
        action_type="READ",
        target_path="sage/experimental/missing.py",
    )
    read_bad_receipt = bridge.execute_c2_request(read_bad_req)
    assert read_bad_receipt.result_status == "FAIL"


def test_execute_command_success():
    """Verify governed TEST / EXECUTE action execution."""
    bridge = C2ExecutionBridge()
    req = C2ExecutionRequest(
        action_type="TEST",
        command="python -c 'print(\"smoke_test_pass\")'",
    )
    receipt = bridge.execute_c2_request(req)
    assert receipt.result_status == "PASS"
    assert "smoke_test_pass" in receipt.stdout_summary
