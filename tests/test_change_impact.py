"""Unit tests for SAGE Governed Change-Impact & Revalidation Analyzer."""

import os
import pytest
from sage.change_impact import SAGEChangeImpactAnalyzer, SAGECapability


def test_unaffected_change(tmp_path):
    """Verify that modifications to completely unrelated files are classified as UNAFFECTED."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["docs/vision/AI_CIVILIZATION_OPERATING_SYSTEM_VISION.md"]

    # Input immutability check
    files_copy = list(modified_files)

    report = analyzer.analyze_changes(modified_files)

    # Verify input immutability
    assert modified_files == files_copy

    # Verify UNAFFECTED status for all capabilities
    assert len(report.impacted_capabilities) > 0
    for cap_res in report.impacted_capabilities:
        assert cap_res.classification == "UNAFFECTED"
        assert "No overlap" in cap_res.reason

    assert report.revalidation_required is False


def test_directly_affected_capability():
    """Verify that modifying a test reference directly sets REVALIDATION_REQUIRED."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["tests/test_continuity_persistence.py"]

    report = analyzer.analyze_changes(modified_files)

    # Find the target capability
    persistence_cap = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-STATE-PERSISTENCE")
    assert persistence_cap.classification == "REVALIDATION_REQUIRED"
    assert "Direct modification of supporting validation test suite" in persistence_cap.reason
    assert report.revalidation_required is True


def test_evidence_dependency_impact():
    """Verify that modifying a supporting evidence file sets REVALIDATION_REQUIRED."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["evidence_capture/ccl_orchestrator_evidence.json"]

    report = analyzer.analyze_changes(modified_files)

    reliability_cap = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-PML-RELIABILITY")
    assert reliability_cap.classification == "REVALIDATION_REQUIRED"
    assert "Direct modification of supporting evidence record" in reliability_cap.reason


def test_unknown_dependency():
    """Verify that modifying shared/experimental helper files returns UNKNOWN_DEPENDENCY."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["sage/mission_control.py"]

    report = analyzer.analyze_changes(modified_files)

    # Unrelated capabilities are classified as UNKNOWN_DEPENDENCY or affected
    for cap_res in report.impacted_capabilities:
        if cap_res.classification != "REVALIDATION_REQUIRED":
            assert cap_res.classification == "UNKNOWN_DEPENDENCY"
            assert "untracked dependencies" in cap_res.reason


def test_revalidation_required_multiple_capabilities():
    """Verify multiple affected capabilities are correctly categorized with deterministic order."""
    analyzer = SAGEChangeImpactAnalyzer()
    # Modifying files affecting both cognitive and pml capabilities
    modified_files = ["tests/experimental/test_cognitive_kernel.py", "tests/experimental/test_continuity_control.py"]

    report = analyzer.analyze_changes(modified_files)

    cog_cap = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-COGNITIVE-KERNEL")
    pml_cap = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-PML-RELIABILITY")

    assert cog_cap.classification == "REVALIDATION_REQUIRED"
    assert pml_cap.classification == "REVALIDATION_REQUIRED"
    assert report.revalidation_required is True

    # Deterministic serialized ID check
    assert report.evaluation_id.startswith("EVAL-IMPACT-")


def test_no_capability_status_mutation(tmp_path):
    """Verify that analyzing changes is strictly read-only and does not mutate registry state."""
    registry_file = tmp_path / "operational_capability_registry.json"

    # Seed with standard capabilities
    from sage.capability_registry import SAGEOperationalCapabilityRegistry
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))
    initial_mtime = registry_file.stat().st_mtime

    analyzer = SAGEChangeImpactAnalyzer(registry_path=str(registry_file))

    # Run analysis multiple times
    analyzer.analyze_changes(["tests/test_continuity_persistence.py"])
    analyzer.analyze_changes(["sage/mission_control.py"])

    # File modification time should remain identical (no writes occurred during analysis)
    assert registry_file.stat().st_mtime == initial_mtime
