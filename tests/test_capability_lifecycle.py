"""Tests for explicit capability lifecycle and incompletion state."""

from sage.capability_registry import SAGECapability


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
