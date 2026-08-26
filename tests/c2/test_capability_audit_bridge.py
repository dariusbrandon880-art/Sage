"""Unit tests for Capability Audit Bridge."""

import pytest
from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry
from sage.c2.capability_audit_bridge import AuditStatus, CapabilityAuditBridge

VALID_SHA = "bcb01b4c73087a38b556942f7c030d5ef855fa3e"


def test_capability_audit_bridge_sweep(tmp_path):
    registry_file = tmp_path / "test_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))

    # Add test capability with existing test reference
    registry.add_capability(
        SAGECapability(
            capability_id="CAP-AUDIT-TEST",
            name="Audit Test Capability",
            description="Test capability",
            implementation_status="IMPLEMENTED",
            validation_status="VALIDATED",
            evidence_references=[],
            test_references=["tests/c2/test_capability_audit_bridge.py"],
            archive_promotion_status="READY",
        )
    )

    bridge = CapabilityAuditBridge(registry=registry)
    rcpt = bridge.perform_capability_audit(exact_git_head=VALID_SHA)

    assert rcpt.total_capabilities_audited >= 1
    assert rcpt.exact_git_head == VALID_SHA
    assert len(rcpt.receipt_hash) == 64
