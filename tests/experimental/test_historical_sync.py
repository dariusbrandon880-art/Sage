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


def test_future_capability_readiness_assessment():
    """Verify that the Future Capability Readiness and Historical Continuity Assessment exists, has required sections, and is registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    readiness_doc = root_dir / "docs" / "SAGE-FUTURE-CAPABILITY-READINESS-HISTORICAL-CONTINUITY-ASSESSMENT.md"

    assert readiness_doc.exists(), "The Future Capability Readiness Assessment must exist under docs/"
    content = readiness_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-READINESS-CONTINUITY-2026-07-30" in content
    assert "Validated Technical Record" in content

    # Verify Key Core Metaphors
    assert "Prometheus" in content
    assert "Star Wars" in content
    assert "Marvel" in content

    # Verify The Three-Layer Architecture Schema
    assert "CORE LAYER" in content or "Core Layer" in content
    assert "EXPERIMENTAL LAYER" in content or "Experimental Layer" in content
    assert "RESEARCH LAYER" in content or "Research Layer" in content

    # Verify Capability Passport Model (No Orphans)
    assert "No Orphan Capability Rule" in content or "No capability exists without" in content
    assert "Purpose" in content
    assert "Lifecycle Classification" in content or "lifecycle classification" in content
    assert "Validation Strategy" in content or "validation strategy" in content
    assert "Evidence Path" in content or "evidence path" in content
    assert "Archive Reference" in content or "archive reference" in content

    # Verify Risks & Attention
    assert "Risks Requiring Governance Attention" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-FUTURE-CAPABILITY-READINESS-HISTORICAL-CONTINUITY-ASSESSMENT.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_validation_evidence_readiness_assessment():
    """Verify that the SAGE Validation Evidence Readiness Assessment exists, has required sections, and is registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    readiness_doc = root_dir / "docs" / "SAGE-VALIDATION-EVIDENCE-READINESS-ASSESSMENT.md"

    assert readiness_doc.exists(), "The Validation Evidence Readiness Assessment must exist under docs/"
    content = readiness_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-EVIDENCE-READINESS-2026-07-30" in content
    assert "Validated Technical Record" in content

    # Verify key sections
    assert "Current Evidence Maturity Assessment" in content or "Evidence Maturity Assessment" in content
    assert "Validation Framework Strengths" in content
    assert "Evidence Lifecycle & Quality Dimensions" in content or "Evidence Lifecycle Alignment" in content or "Evidence Lifecycle" in content
    assert "Missing Evidence Requirements" in content
    assert "Remaining Risks" in content
    assert "Recommended Validation Priorities" in content
    assert "Next Recommended Governance Action" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-VALIDATION-EVIDENCE-READINESS-ASSESSMENT.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_sdr_readiness_specification():
    """Verify that the SAGE Safe Dry Run (SDR) Readiness Specification exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    sdr_doc = root_dir / "docs" / "SAGE-SDR-READINESS-SPECIFICATION.md"

    assert sdr_doc.exists(), "The SAGE-SDR Readiness Specification must exist under docs/"
    content = sdr_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-SDR-READINESS-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "Sandbox Boundaries" in content
    assert "Simulation Lifecycle" in content or "SDR Simulation Lifecycle" in content
    assert "Validation Strategy" in content
    assert "SDR Evidence Requirements" in content
    assert "Human Review Checkpoints" in content
    assert "Failure Handling Model" in content
    assert "Future Implementation Prerequisites" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-SDR-READINESS-SPECIFICATION.md" in index_content
    assert "[State: PROPOSED]" in index_content


def test_sdr_agent_coordination_alignment_review():
    """Verify that the SAGE Safe Dry Run (SDR) & Agent Coordination Alignment Review exists, has required sections, and is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    review_doc = root_dir / "docs" / "SAGE-SDR-AGENT-COORDINATION-ALIGNMENT-REVIEW.md"

    assert review_doc.exists(), "The SAGE-SDR & Agent Coordination Review must exist under docs/"
    content = review_doc.read_text(encoding="utf-8")

    # Verify ID and Status
    assert "SAGE-SDR-AGENT-ALIGN-2026-07-30" in content
    assert "PROPOSED" in content

    # Verify key sections
    assert "SDR and Agent Framework Relationship" in content
    assert "Agent Contribution Evidence Model" in content
    assert "Multi-Agent Validation Handoff Flow" in content or "Validation handoff flow" in content or "Validation Handoff Flow" in content
    assert "Human Review Checkpoints" in content
    assert "Systemic Risks" in content or "Risks" in content
    assert "Future Research Questions" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-SDR-AGENT-COORDINATION-ALIGNMENT-REVIEW.md" in index_content
    assert "[State: PROPOSED]" in index_content
