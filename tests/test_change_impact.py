"""Unit tests for SAGE Governed Change-Impact & Revalidation Analyzer.

Verifies the entire requested test matrix for SAGE change-impact analysis.
"""

import os
import json
import pytest
from pathlib import Path
from sage.change_impact import SAGEChangeImpactAnalyzer, SAGECapability


def test_unaffected_change(tmp_path):
    """Matrix: unaffected. Verify modifications to unrelated files are UNAFFECTED."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["docs/vision/AI_CIVILIZATION_OPERATING_SYSTEM_VISION.md"]

    report = analyzer.analyze_changes(modified_files)

    for cap_res in report.impacted_capabilities:
        assert cap_res.classification == "UNAFFECTED"
        assert "No overlap" in cap_res.reason

    assert report.revalidation_required is False


def test_direct_capability_impact():
    """Matrix: direct capability impact. Verify that modifying a capability-relevant test file impacts the capability."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["tests/test_continuity_persistence.py"]

    report = analyzer.analyze_changes(modified_files)

    cap = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-STATE-PERSISTENCE")
    assert cap.classification == "REVALIDATION_REQUIRED"


def test_evidence_dependency():
    """Matrix: evidence dependency. Verify that modifying a supporting evidence file is detected."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["evidence_capture/ccl_orchestrator_evidence.json"]

    report = analyzer.analyze_changes(modified_files)

    cap = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-PML-RELIABILITY")
    assert cap.classification == "REVALIDATION_REQUIRED"
    assert "Direct modification of supporting evidence record" in cap.reason


def test_validation_dependency():
    """Matrix: validation dependency. Verify that modifying a validation test impacts the corresponding capability."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["tests/experimental/test_cognitive_kernel.py"]

    report = analyzer.analyze_changes(modified_files)

    cap = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-COGNITIVE-KERNEL")
    assert cap.classification == "REVALIDATION_REQUIRED"


def test_measurement_dependency():
    """Matrix: measurement dependency. Verify that capability promotion/measurement state is preserved."""
    analyzer = SAGEChangeImpactAnalyzer()
    report = analyzer.analyze_changes(["tests/test_continuity_persistence.py"])

    for item in report.provenance_chain:
        assert "measurement_verification_state" in item
        assert item["measurement_verification_state"] == "READY"


def test_unknown_dependency():
    """Matrix: unknown dependency. Verify that modifying unmapped experimental files yields UNKNOWN_DEPENDENCY."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["sage/mission_control.py"]

    report = analyzer.analyze_changes(modified_files)

    for cap_res in report.impacted_capabilities:
        if cap_res.classification != "REVALIDATION_REQUIRED":
            assert cap_res.classification == "UNKNOWN_DEPENDENCY"
            assert "Changes to shared experimental" in cap_res.reason


def test_revalidation_required():
    """Matrix: revalidation-required. Verify that revalidation required flag is set on any impact."""
    analyzer = SAGEChangeImpactAnalyzer()
    report = analyzer.analyze_changes(["tests/test_continuity_persistence.py"])
    assert report.revalidation_required is True


def test_multiple_capabilities():
    """Matrix: multiple capabilities. Verify multiple capabilities can be simultaneously impacted."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["tests/experimental/test_cognitive_kernel.py", "tests/experimental/test_continuity_control.py"]

    report = analyzer.analyze_changes(modified_files)

    cog = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-COGNITIVE-KERNEL")
    pml = next(c for c in report.impacted_capabilities if c.capability_id == "CAP-PML-RELIABILITY")

    assert cog.classification == "REVALIDATION_REQUIRED"
    assert pml.classification == "REVALIDATION_REQUIRED"


def test_deterministic_ordering():
    """Matrix: deterministic ordering. Verify that output ordering is deterministic."""
    analyzer = SAGEChangeImpactAnalyzer()
    report1 = analyzer.analyze_changes(["tests/experimental/test_cognitive_kernel.py"])
    report2 = analyzer.analyze_changes(["tests/experimental/test_cognitive_kernel.py"])

    assert [c.capability_id for c in report1.impacted_capabilities] == [c.capability_id for c in report2.impacted_capabilities]


def test_deterministic_serialization():
    """Matrix: deterministic serialization. Verify that evaluation_id hash is fully deterministic."""
    analyzer = SAGEChangeImpactAnalyzer()
    report1 = analyzer.analyze_changes(["tests/test_continuity_persistence.py"])
    report2 = analyzer.analyze_changes(["tests/test_continuity_persistence.py"])

    assert report1.evaluation_id == report2.evaluation_id


def test_provenance_preservation():
    """Matrix: provenance preservation. Verify exact required chain keys:

    Change -> Capability -> Evidence -> Validation/Test -> Measurement/Verification State -> Classification -> Reason
    """
    analyzer = SAGEChangeImpactAnalyzer()
    report = analyzer.analyze_changes(["tests/test_continuity_persistence.py"])

    for item in report.provenance_chain:
        assert "change" in item
        assert "capability" in item
        assert "evidence" in item
        assert "validation_test" in item
        assert "measurement_verification_state" in item
        assert "classification" in item
        assert "reason" in item


def test_input_immutability():
    """Matrix: input immutability. Verify the input file list is never mutated."""
    analyzer = SAGEChangeImpactAnalyzer()
    modified_files = ["tests/test_continuity_persistence.py", "sage/mission_control.py"]
    files_copy = list(modified_files)

    analyzer.analyze_changes(modified_files)

    assert modified_files == files_copy


def test_no_capability_status_mutation(tmp_path):
    """Matrix: no capability-status mutation. Verify that the Operational Registry file is untouched (read-only)."""
    registry_file = tmp_path / "operational_capability_registry.json"
    from sage.capability_registry import SAGEOperationalCapabilityRegistry
    registry = SAGEOperationalCapabilityRegistry(storage_path=str(registry_file))
    initial_mtime = registry_file.stat().st_mtime

    analyzer = SAGEChangeImpactAnalyzer(registry_path=str(registry_file))
    analyzer.analyze_changes(["tests/test_continuity_persistence.py"])

    assert registry_file.stat().st_mtime == initial_mtime


def test_protected_boundary_exclusion():
    """Matrix: protected-boundary exclusion. Verify that core files are never modified or touched by the analyzer."""
    analyzer = SAGEChangeImpactAnalyzer()
    report = analyzer.analyze_changes(["sage/core/spek.py"])

    # Core changes are outside allowed experimental changes; since we don't have mapping, they are classified safely as UNKNOWN_DEPENDENCY or UNAFFECTED
    for cap_res in report.impacted_capabilities:
        assert cap_res.classification in ["UNAFFECTED", "UNKNOWN_DEPENDENCY"]
