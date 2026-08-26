"""Unit and integration tests for SAGE C2 Capability Audit Bridge & Drift Sentinel."""

import pytest
import tempfile
import shutil
from pathlib import Path

from sage.c2.capability_audit_bridge import (
    AuditStatus,
    C2CapabilityAuditBridge,
    CapabilityAuditReceipt,
)
from sage.c2.capability_warehouse import CapabilityWarehouseEngine
from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry


@pytest.fixture
def temp_op_registry_path(tmp_path):
    dest = tmp_path / "temp_op_registry.json"
    shutil.copy("evidence_capture/operational_capability_registry.json", dest)
    return str(dest)


@pytest.fixture
def temp_warehouse_path(tmp_path):
    return str(tmp_path / "temp_warehouse_registry.json")


@pytest.fixture
def valid_sha():
    return "0035e9e5977ff1bf8b0d12030789c39c7cf069d8"


def test_capability_audit_success(temp_op_registry_path, temp_warehouse_path, valid_sha):
    registry = SAGEOperationalCapabilityRegistry(storage_path=temp_op_registry_path)
    warehouse = CapabilityWarehouseEngine(
        storage_path=temp_warehouse_path,
        op_registry_path=temp_op_registry_path,
    )

    bridge = C2CapabilityAuditBridge(op_registry=registry, warehouse_engine=warehouse)
    receipt = bridge.audit_capabilities(exact_git_head=valid_sha)

    assert receipt.exact_git_head == valid_sha
    assert receipt.total_capabilities_audited > 0
    assert receipt.verified_count == receipt.total_capabilities_audited
    assert receipt.drift_count == 0
    assert receipt.audit_verdict == "PASS"
    assert len(receipt.receipt_hash) == 64


def test_invalid_sha_rejection(temp_op_registry_path, temp_warehouse_path):
    registry = SAGEOperationalCapabilityRegistry(storage_path=temp_op_registry_path)
    warehouse = CapabilityWarehouseEngine(
        storage_path=temp_warehouse_path,
        op_registry_path=temp_op_registry_path,
    )

    bridge = C2CapabilityAuditBridge(op_registry=registry, warehouse_engine=warehouse)

    with pytest.raises(ValueError, match="Invalid exact git HEAD commit SHA"):
        bridge.audit_capabilities(exact_git_head="short_sha_123")


def test_missing_proof_file_fails_closed(temp_op_registry_path, temp_warehouse_path, valid_sha):
    registry = SAGEOperationalCapabilityRegistry(storage_path=temp_op_registry_path)
    warehouse = CapabilityWarehouseEngine(
        storage_path=temp_warehouse_path,
        op_registry_path=temp_op_registry_path,
    )

    # Inject dummy capability with non-existent evidence reference
    dummy_cap = SAGECapability(
        capability_id="CAP-DUMMY-DRIFT",
        name="Dummy Drift Capability",
        description="Capability referencing non-existent file on disk",
        evidence_references=["evidence_capture/non_existent_file_xyz.json"],
        test_references=["tests/test_continuity_persistence.py"],
    )
    registry.add_capability(dummy_cap)

    bridge = C2CapabilityAuditBridge(op_registry=registry, warehouse_engine=warehouse)
    receipt = bridge.audit_capabilities(exact_git_head=valid_sha)

    assert receipt.audit_verdict == "DRIFT_DETECTED"
    assert receipt.drift_count >= 1

    drift_record = next(r for r in receipt.audit_records if r.capability_id == "CAP-DUMMY-DRIFT")
    assert drift_record.audit_status == AuditStatus.MISSING_PROOF
    assert drift_record.evidence_files_present is False
