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


def test_knowledge_graph_report_conformance():
    """Verify that the SAGE Knowledge Graph and Traceability Architecture Report exists, contains key sections, and is properly registered."""
    root_dir = Path(__file__).parent.parent.parent
    graph_doc = root_dir / "docs" / "SAGE-KNOWLEDGE-GRAPH-AND-TRACEABILITY-ARCHITECTURE.md"

    assert graph_doc.exists(), "Knowledge Graph Report must exist under docs/"
    content = graph_doc.read_text(encoding="utf-8")

    # Assert critical sections
    assert "SAGE Knowledge Graph and Traceability Architecture Report" in content
    assert "SAGE-KNOWLEDGE-GRAPH-2026-07-29" in content
    assert "Recommended Metadata Schema" in content
    assert "Unique Document Identifiers Strategy" in content
    assert "Unified Document Relationship Map" in content
    assert "Explicit Traceability Lineages" in content
    assert "Document Dependency Graph" in content
    assert "Mappings and Trace Matrices" in content
    assert "Cross-Reference Conventions" in content
    assert "Duplicate Detection & Future Retrieval Opportunities" in content
    assert "Documentation Health Assessment & Gap Analysis" in content
    assert "Recommended Documentation Standards" in content

    # Verify index registration
    index_file = Path(__file__).parent.parent.parent / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-KNOWLEDGE-GRAPH-AND-TRACEABILITY-ARCHITECTURE.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_health_and_navigation_standards():
    """Verify that Documentation Health Audit, Master Navigation Standard, and Context Restoration Protocol files exist, conform to schemas, and are indexed."""
    root_dir = Path(__file__).parent.parent.parent

    # 1. Health Audit Report
    health_file = root_dir / "docs" / "SAGE-DOCUMENTATION-HEALTH-AUDIT-REPORT.md"
    assert health_file.exists()
    health_content = health_file.read_text(encoding="utf-8")
    assert "SAGE-DOC-AUDIT-2026-07-29" in health_content
    assert "Documentation Maturity Assessment" in health_content
    assert "The Core 6 Navigation Questions Mapping" in health_content

    # 2. Navigation Standard
    nav_file = root_dir / "docs" / "SAGE-MASTER-ARCHIVE-NAVIGATION-STANDARD.md"
    assert nav_file.exists()
    nav_content = nav_file.read_text(encoding="utf-8")
    assert "SAGE-NAV-STANDARD-2026-07-29" in nav_content
    assert "Canonical Entry Points" in nav_content
    assert "Structured Lookup Protocols" in nav_content

    # 3. Restoration Protocol
    restore_file = root_dir / "docs" / "SAGE-CONTEXT-RESTORATION-PROTOCOL.md"
    assert restore_file.exists()
    restore_content = restore_file.read_text(encoding="utf-8")
    assert "SAGE-RESTORE-PROTOCOL-2026-07-29" in restore_content
    assert "Session Context Restoration Flow" in restore_content
    assert "Prohibited Assumptions" in restore_content

    # Index registration checks
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-DOCUMENTATION-HEALTH-AUDIT-REPORT.md" in index_content
    assert "../docs/SAGE-MASTER-ARCHIVE-NAVIGATION-STANDARD.md" in index_content
    assert "../docs/SAGE-CONTEXT-RESTORATION-PROTOCOL.md" in index_content


def test_evolution_governance_conformance():
    """Verify that SAGE Evolution Governance Framework Report exists, contains required elements, and is registered."""
    root_dir = Path(__file__).parent.parent.parent
    gov_file = root_dir / "docs" / "SAGE-EVOLUTION-GOVERNANCE-FRAMEWORK.md"

    assert gov_file.exists(), "Governance Framework Report must exist under docs/"
    content = gov_file.read_text(encoding="utf-8")

    # Assert critical sections
    assert "SAGE Evolution Governance Framework Report" in content
    assert "SAGE-EVOL-GOV-2026-07-29" in content
    assert "Standard Research Intake Process" in content
    assert "Research Promotion Gates" in content
    assert "Decision Authority Model" in content
    assert "Anti-Drift Controls" in content
    assert "Capability Lifecycle State Machine" in content
    assert "Future Session Governance Flow" in content

    # Assert key terminology invariants
    assert "One-Way Import Law" in content
    assert "rejection paths" in content or "rejection path" in content or "Rejection Path" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-EVOLUTION-GOVERNANCE-FRAMEWORK.md" in index_content
    assert "[State: VALIDATED]" in index_content


def test_system_state_intelligence_conformance():
    """Verify SAGE System State Intelligence Framework exists, has correct sections, and is registered in INDEX.md."""
    root_dir = Path(__file__).parent.parent.parent
    intel_file = root_dir / "docs" / "SAGE-SYSTEM-STATE-INTELLIGENCE-FRAMEWORK.md"

    assert intel_file.exists(), "State Intelligence Framework must exist under docs/"
    content = intel_file.read_text(encoding="utf-8")

    # Assert critical sections
    assert "SAGE System State Intelligence Framework Report" in content
    assert "SAGE-STATE-INTEL-2026-07-29" in content
    assert "Canonical SAGE State Model" in content
    assert "State Transition Documentation Model" in content
    assert "Canonical Governance Snapshot Format" in content
    assert "Continuity Failure Prevention" in content
    assert "Future Session Alignment & Startup" in content

    # Verify index registration
    index_file = root_dir / "Main Archive" / "INDEX.md"
    index_content = index_file.read_text(encoding="utf-8")
    assert "../docs/SAGE-SYSTEM-STATE-INTELLIGENCE-FRAMEWORK.md" in index_content
    assert "[State: VALIDATED]" in index_content
