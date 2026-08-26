"""Unit and integration tests for SAGE Dynamic Targeted Test Orchestrator."""

import pytest
import subprocess
from sage.c2.targeted_test_executor import (
    TargetedTestExecutionReceipt,
    TargetedTestExecutor,
)


@pytest.fixture
def executor():
    return TargetedTestExecutor()


@pytest.fixture
def valid_sha():
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def test_targeted_test_selection_direct(executor):
    modified = ["tests/test_continuity_persistence.py"]
    tests, is_fallback = executor.select_tests_for_changes(modified)

    assert is_fallback is False
    assert tests == ["tests/test_continuity_persistence.py"]


def test_ambiguity_fallback_on_unknown_dependency(executor):
    modified = ["sage/mission_control.py"]
    tests, is_fallback = executor.select_tests_for_changes(modified)

    assert is_fallback is True
    assert tests == ["tests/"]


def test_empty_modified_files_fallback(executor):
    tests, is_fallback = executor.select_tests_for_changes([])

    assert is_fallback is True
    assert tests == ["tests/"]


def test_invalid_sha_rejection(executor):
    with pytest.raises(ValueError, match="Invalid exact git HEAD commit SHA"):
        executor.execute_targeted_tests(
            modified_files=["tests/test_continuity_persistence.py"],
            exact_git_head="short_sha_123",
        )


def test_receipt_hash_computation(valid_sha):
    receipt = TargetedTestExecutionReceipt(
        receipt_id="test_rec_123",
        wave_id="targeted_test_wave_001",
        exact_git_head=valid_sha,
        modified_files=["tests/test_continuity_persistence.py"],
        selected_test_files=["tests/test_continuity_persistence.py"],
        fallback_to_full_suite=False,
        tests_executed=10,
        tests_passed=10,
        tests_failed=0,
        execution_time_seconds=0.15,
        verdict="PASS",
    )
    receipt.receipt_hash = receipt.compute_hash()

    assert len(receipt.receipt_hash) == 64
    assert receipt.verdict == "PASS"
