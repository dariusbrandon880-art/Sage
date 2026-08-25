"""Tests for explicit capability lifecycle and incompletion state."""

from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry


def test_partial_capability_preserves_incompletion_reason_and_dependencies():
    capability = SAGECapability(
        capability_id="CAP-TEST-PARTIAL",
        name="Partial Capability",
        description="Test capability",
        lifecycle_status="PARTIAL",
        dependencies=["CAP-DEPENDENCY"],
        incompletion_reason="Evidence is incomplete",
    )

    assert capability.lifecycle_status == "PARTIAL"
    assert capability.dependencies == ["CAP-DEPENDENCY"]
    assert capability.incompletion_reason == "Evidence is incomplete"


def test_registry_persists_and_retrieves_capability_lifecycle(tmp_path):
    storage_path = tmp_path / "test_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(storage_path))

    cap = SAGECapability(
        capability_id="CAP-LIFECYCLE-TEST",
        name="Lifecycle Test Capability",
        description="Verifies lifecycle persistence",
        lifecycle_status="PARTIAL",
        dependencies=["CAP-COGNITIVE-KERNEL"],
        incompletion_reason="Pending verification receipt",
    )
    registry.add_capability(cap)

    registry2 = SAGEOperationalCapabilityRegistry(storage_path=str(storage_path))
    retrieved = registry2.get_capability("CAP-LIFECYCLE-TEST")

    assert retrieved is not None
    assert retrieved.lifecycle_status == "PARTIAL"
    assert retrieved.dependencies == ["CAP-COGNITIVE-KERNEL"]
    assert retrieved.incompletion_reason == "Pending verification receipt"
