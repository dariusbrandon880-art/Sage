"""Unit test suite for SAGE Change-Impact & Revalidation Analyzer (SAGE-CIRA)."""

import pytest
from sage.experimental.act.capability_passport import CapabilityPassport
from sage.experimental.change_impact import SAGEChangeImpactAnalyzer


def test_change_impact_direct_and_transitive():
    """Verify direct, transitive, unaffected, and unknown dependency classification."""
    p_core = CapabilityPassport(
        name="CAP-COGNITIVE-KERNEL",
        purpose="Simulates safety gate checks",
        validation_strategy="cognitive_test",
        evidence_path="evidence_capture/cognitive_kernel_foundation_report.json",
        archive_location="INDEX.md"
    )
    p_direct = CapabilityPassport(
        name="CAP-PML-RELIABILITY",
        purpose="Task state persistence and sequence tracking",
        dependencies=["CAP-COGNITIVE-KERNEL"],  # Direct dependent of core
        validation_strategy="pml_test",
        evidence_path="evidence_capture/pml_reliability.json",
        archive_location="INDEX.md"
    )
    p_transitive = CapabilityPassport(
        name="CAP-CONTROL-TOWER",
        purpose="Continuous loop health monitoring",
        dependencies=["CAP-PML-RELIABILITY"],  # Transitive dependent of core
        validation_strategy="tower_test",
        evidence_path="evidence_capture/tower_health.json",
        archive_location="INDEX.md"
    )
    p_unaffected = CapabilityPassport(
        name="CAP-DEMO-LAUNCHER",
        purpose="Dry run scenario execution",
        dependencies=[],  # Unaffected
        validation_strategy="demo_test",
        evidence_path="evidence_capture/demo_launcher_evidence.json",
        archive_location="INDEX.md"
    )

    analyzer = SAGEChangeImpactAnalyzer([p_core, p_direct, p_transitive, p_unaffected])

    # 1. Analyze impact of CAP-COGNITIVE-KERNEL changing
    report = analyzer.analyze_impact("CAP-COGNITIVE-KERNEL")

    assert report["status"] == "ANALYZED"
    assert report["impacted_capabilities_count"] == 2
    assert report["revalidation_required_files_count"] == 2
    assert report["revalidation_required_files"] == [
        "evidence_capture/pml_reliability.json",
        "evidence_capture/tower_health.json"
    ]

    assessments = report["assessments"]

    # Check 7-tier evaluation chain for CAP-PML-RELIABILITY (Direct)
    assert assessments["CAP-PML-RELIABILITY"]["change_origin"] == "CAP-COGNITIVE-KERNEL"
    assert assessments["CAP-PML-RELIABILITY"]["affected_capability"] == "CAP-PML-RELIABILITY"
    assert assessments["CAP-PML-RELIABILITY"]["supporting_evidence"] == "evidence_capture/pml_reliability.json"
    assert assessments["CAP-PML-RELIABILITY"]["validation_test"] == "pml_test"
    assert assessments["CAP-PML-RELIABILITY"]["measurement_verification_state"] == "PROPOSED_PASSPORT"
    assert assessments["CAP-PML-RELIABILITY"]["classification"] == "REVALIDATION_REQUIRED"
    assert "Directly depends on" in assessments["CAP-PML-RELIABILITY"]["reason"]

    # Check 7-tier evaluation chain for CAP-CONTROL-TOWER (Transitive)
    assert assessments["CAP-CONTROL-TOWER"]["change_origin"] == "CAP-COGNITIVE-KERNEL"
    assert assessments["CAP-CONTROL-TOWER"]["affected_capability"] == "CAP-CONTROL-TOWER"
    assert assessments["CAP-CONTROL-TOWER"]["supporting_evidence"] == "evidence_capture/tower_health.json"
    assert assessments["CAP-CONTROL-TOWER"]["validation_test"] == "tower_test"
    assert assessments["CAP-CONTROL-TOWER"]["classification"] == "REVALIDATION_REQUIRED"
    assert "Transitively depends on" in assessments["CAP-CONTROL-TOWER"]["reason"]

    # Unaffected
    assert assessments["CAP-DEMO-LAUNCHER"]["classification"] == "UNAFFECTED"

    # 2. Unknown dependency analysis
    unknown_report = analyzer.analyze_impact("CAP-NONEXISTENT")
    assert unknown_report["status"] == "UNKNOWN_DEPENDENCY"
    assert unknown_report["assessments"]["CAP-NONEXISTENT"]["classification"] == "UNKNOWN_DEPENDENCY"

    # Ensure input immutability and no status mutation of passports
    assert p_core.lifecycle_state == "PROPOSED"
    assert p_direct.lifecycle_state == "PROPOSED"
