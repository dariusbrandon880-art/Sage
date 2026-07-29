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
