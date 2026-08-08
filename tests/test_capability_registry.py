"""Unit tests for SAGE Operational Capability Registry."""

import os
import json
import pytest
from pathlib import Path

from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry


def test_capability_registry_defaults(tmp_path):
    """Verify that SAGEOperationalCapabilityRegistry seeds default capabilities correctly on empty initialization."""
    registry_file = tmp_path / "operational_capability_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))

    # Check that defaults were seeded and file exists
    assert registry_file.exists()
    capabilities = registry.list_capabilities()
    assert len(capabilities) == 7

    # Verify that CAP-COGNITIVE-KERNEL and CAP-PML-RELIABILITY are present
    cognitive_kernel = registry.get_capability("CAP-COGNITIVE-KERNEL")
    assert cognitive_kernel is not None
    assert cognitive_kernel.name == "Cognitive Kernel Foundation"
    assert cognitive_kernel.validation_status == "VALIDATED"
    assert "tests/experimental/test_cognitive_kernel.py" in cognitive_kernel.test_references
    assert cognitive_kernel.archive_promotion_status == "READY"

    pml_reliability = registry.get_capability("CAP-PML-RELIABILITY")
    assert pml_reliability is not None
    assert pml_reliability.name == "PML Operational Reliability"


def test_capability_registry_lookup_by_name(tmp_path):
    """Verify registry search lookup capability by human-readable name."""
    registry_file = tmp_path / "operational_capability_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))

    # Match case-insensitive lookup
    cap = registry.lookup_by_name("cognitive kernel foundation")
    assert cap is not None
    assert cap.capability_id == "CAP-COGNITIVE-KERNEL"

    # Match exact lookup
    cap_exact = registry.lookup_by_name("State Persistence")
    assert cap_exact is not None
    assert cap_exact.capability_id == "CAP-STATE-PERSISTENCE"

    # Lookup non-existent name
    assert registry.lookup_by_name("Non-existent Capability") is None


def test_add_custom_capability(tmp_path):
    """Verify adding, updating, and saving new custom capabilities."""
    registry_file = tmp_path / "operational_capability_registry.json"
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))

    new_cap = SAGECapability(
        capability_id="CAP-OPERATIONAL-REGISTRY",
        name="Operational Capability Registry",
        description="Tracks implemented and validated capabilities in SAGE.",
        implementation_status="IMPLEMENTED",
        validation_status="VALIDATED",
        evidence_references=["evidence_capture/operational_capability_registry.json"],
        test_references=["tests/test_capability_registry.py"],
        archive_promotion_status="READY"
    )

    registry.add_capability(new_cap)

    # Reload from disk using a fresh instance to ensure persistence
    fresh_registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))
    retrieved_cap = fresh_registry.get_capability("CAP-OPERATIONAL-REGISTRY")

    assert retrieved_cap is not None
    assert retrieved_cap.name == "Operational Capability Registry"
    assert retrieved_cap.implementation_status == "IMPLEMENTED"
    assert retrieved_cap.validation_status == "VALIDATED"
    assert "tests/test_capability_registry.py" in retrieved_cap.test_references
    assert retrieved_cap.archive_promotion_status == "READY"


def test_corrupted_file_fallback(tmp_path):
    """Verify fallback behavior to default capabilities when JSON is corrupted."""
    registry_file = tmp_path / "operational_capability_registry.json"

    # Write corrupt JSON content
    with open(registry_file, "w") as f:
        f.write("{invalid-json-content")

    # Initialization should fall back gracefully and re-seed
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))
    assert len(registry.list_capabilities()) == 7
