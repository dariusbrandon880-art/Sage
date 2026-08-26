from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry
from sage.c2.capability_audit_bridge import CapabilityAuditBridge

VALID_SHA = "7cdebce6e542ab5e8975194c6610f388e83942a9"

def test_audit_bridge_verifies_existing_test_reference(tmp_path):
    registry=SAGEOperationalCapabilityRegistry(storage_path=str(tmp_path/"registry.json"))
    registry.add_capability(SAGECapability(capability_id="CAP-AUDIT-TEST",name="Audit Test Capability",description="Test capability",implementation_status="IMPLEMENTED",validation_status="VALIDATED",evidence_references=[],test_references=["tests/c2/test_capability_audit_bridge.py"],archive_promotion_status="READY"))
    rcpt=CapabilityAuditBridge(registry=registry).perform_capability_audit(exact_git_head=VALID_SHA)
    assert rcpt.total_capabilities_audited >= 1 and rcpt.exact_git_head == VALID_SHA and len(rcpt.receipt_hash)==64
