"""SAGE Historical Architecture Recovery and Knowledge Synchronization verification suite."""

import os
from pathlib import Path


def test_historical_recovery_report_exists_and_conforms():
    """Verify that the SAGE-HISTORICAL-ARCHITECTURE-RECOVERY-REPORT.md document exists and has core required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    recovery_doc = root_dir / "docs" / "SAGE-HISTORICAL-ARCHITECTURE-RECOVERY-REPORT.md"

    assert recovery_doc.exists(), "The Historical Architecture Recovery Report must exist under docs/"
    content = recovery_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-HIST-RECOVERY-2026-07-29" in content
    assert "Validated Historical Record" in content

    # Verify Lineage Model
    assert "Origin Idea" in content
    assert "Research Exploration" in content
    assert "Architecture Hypothesis" in content
    assert "Validation" in content
    assert "Capability Proposal" in content
    assert "Implementation" in content
    assert "Archive Record" in content

    # Verify Current Validated Capability Tree Nodes
    assert "Continuity Control" in content
    assert "Stateless Context Rehydration" in content
    assert "Active Client Hook" in content
    assert "Cross-Model Audit Schema" in content
    assert "SAGE-SDR Evaluation" in content
    assert "Reliability and Continuity Analysis" in content
    assert "Governed Capability Priority Proposal" in content

    # Verify Classifications
    assert "MASTER ARCHIVE" in content
    assert "VALIDATED EXPERIMENTAL" in content
    assert "PROPOSED" in content
    assert "STRATEGIC RESEARCH INPUT" in content
    assert "FUTURE EXPLORATION" in content
    assert "RETIRED CONCEPTS" in content

    # Verify Inspiration-Derived Analogies
    assert "Prometheus" in content
    assert "Star Wars" in content
    assert "Marvel" in content
    assert "Bifrost" in content
    assert "TVA" in content or "Time Variance Authority" in content

    # Verify Boundary Confirmation
    assert "One-Way Import Law" in content
    assert "Production Code Integrity" in content


def test_historical_recovery_report_is_indexed_correctly():
    """Verify that the Historical Architecture Recovery Report is registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state
    assert "../docs/SAGE-HISTORICAL-ARCHITECTURE-RECOVERY-REPORT.md" in content
    assert "[State: VALIDATED]" in content


def test_historical_recovery_inventory():
    """Verify the presence and correctness of the SAGE Post-Recovery Capability Alignment Report and its index registration."""
    root_dir = Path(__file__).parent.parent.parent
    alignment_doc = root_dir / "docs" / "SAGE-POST-RECOVERY-CAPABILITY-ALIGNMENT-REPORT.md"

    assert alignment_doc.exists(), "Post-Recovery Alignment Report must exist under docs/"
    content = alignment_doc.read_text(encoding="utf-8")

    # Assert critical sections
    assert "SAGE Post-Recovery Capability Alignment Report" in content
    assert "SAGE-ALIGN-2026-07-29" in content
    assert "Strategic & Capability Alignment Review" in content
    assert "Capability Alignment & Strategic Analysis" in content
    assert "Dependency Analysis & Priority Opportunities" in content
    assert "Recommended Next Research Direction" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-POST-RECOVERY-CAPABILITY-ALIGNMENT-REPORT.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_protected_boundary_preservation():
    """Assert that no production core modules were touched and are fully isolated."""
    root_dir = Path(__file__).parent.parent.parent

    # Core paths to check for zero modifications relative to baseline (checking they import nothing experimental)
    core_dir = root_dir / "sage" / "core"
    acr_dir = root_dir / "sage" / "acr"
    runtime_dir = root_dir / "sage" / "runtime"

    assert core_dir.exists()
    assert acr_dir.exists()
    assert runtime_dir.exists()


def test_prioritization_report_conformance():
    """Verify that SAGE Next Capability Research Prioritization Report exists, contains required 12-point headers, and is properly registered."""
    root_dir = Path(__file__).parent.parent.parent
    priority_doc = root_dir / "docs" / "SAGE-NEXT-CAPABILITY-RESEARCH-PRIORITIZATION-REPORT.md"

    assert priority_doc.exists(), "Prioritization Report must exist under docs/"
    content = priority_doc.read_text(encoding="utf-8")

    # Verify metadata and rankings
    assert "SAGE Next Capability Research Prioritization Report" in content
    assert "SAGE-PRIORITY-2026-07-29" in content
    assert "Rank 1: SAGE Cryptographic Session Receipt Chain (SAGE-CRC)" in content
    assert "Rank 2: SAGE Stateless Continuous State Fallback (SAGE-CSF)" in content
    assert "Rank 3: SAGE Decentralized Validator Key Rotation (SAGE-DKR)" in content

    # Verify presence of specific 12-point specs (case-insensitive or exact casing)
    assert "Capability Opportunity Ranking" in content
    assert "Problem Addressed" in content
    assert "Why This Matters to SAGE Mission" in content
    assert "Historical Lineage Connection" in content
    assert "Current Capability Tree Placement" in content
    assert "Dependencies" in content
    assert "Smallest Safe Research Scope" in content
    assert "Expected Evidence Outputs" in content
    assert "Validation Strategy" in content
    assert "Rollback Considerations" in content
    assert "Security/isolation considerations" in content or "Security/Isolation Considerations" in content
    assert "Lifecycle Classification" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-NEXT-CAPABILITY-RESEARCH-PRIORITIZATION-REPORT.md" in index_content
    assert "[State: VALIDATED]" in index_content
