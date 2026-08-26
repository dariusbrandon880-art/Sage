"""Unit tests for Governed C2 Execution Surface Engine."""

import pytest
from sage.c2.c2_execution_surface import (
    C2CommandType,
    C2ExecutionRequest,
    C2ExecutionSurfaceEngine,
)

VALID_SHA = "bcb01b4c73087a38b556942f7c030d5ef855fa3e"


def test_c2_execution_surface_success():
    engine = C2ExecutionSurfaceEngine()
    req = C2ExecutionRequest(
        request_id="req-001",
        command_type=C2CommandType.READ,
        target_path="sage/c2/c2_execution_surface.py",
        starting_git_head=VALID_SHA,
    )

    rcpt = engine.execute_request(req)

    assert rcpt.status == "SUCCESS"
    assert rcpt.starting_git_head == VALID_SHA
    assert len(rcpt.receipt_hash) == 64


def test_c2_execution_surface_protected_namespace_rejection():
    engine = C2ExecutionSurfaceEngine()
    req = C2ExecutionRequest(
        request_id="req-002",
        command_type=C2CommandType.WRITE,
        target_path="sage/core/spek.py",
        starting_git_head=VALID_SHA,
    )

    rcpt = engine.execute_request(req)

    assert rcpt.status == "REJECTED_PROTECTED_NAMESPACE"
    assert "protected namespace" in rcpt.rejection_reason


def test_c2_execution_surface_invalid_sha_rejection():
    engine = C2ExecutionSurfaceEngine()
    req = C2ExecutionRequest(
        request_id="req-003",
        command_type=C2CommandType.READ,
        target_path="sage/c2/c2_execution_surface.py",
        starting_git_head="shortsha123",
    )

    rcpt = engine.execute_request(req)

    assert rcpt.status == "REJECTED_INVALID_SHA"
