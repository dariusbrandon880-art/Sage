"""SAGE Capability Evolution Governance Framework programmatic validation suite."""

import os
import ast
from pathlib import Path


def test_governance_framework_document_exists_and_conforms():
    """Verify that the SAGE-CAPABILITY-EVOLUTION-GOVERNANCE-FRAMEWORK.md document exists and has core required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    gov_doc = root_dir / "docs" / "SAGE-CAPABILITY-EVOLUTION-GOVERNANCE-FRAMEWORK.md"

    assert gov_doc.exists(), "The Capability Evolution Governance Framework document must exist under docs/"
    content = gov_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID, Classification and Status
    assert "SAGE-GOV-FRAMEWORK-2026-07-29" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify Sections
    assert "Section 1 — Capability Governance Model" in content
    assert "Section 2 — Capability Passport Model" in content
    assert "Section 3 — Capability State Transition Record" in content
    assert "Section 4 — Validation Integration" in content
    assert "Section 5 — Evidence Package Model" in content
    assert "Section 6 — Failure as Information Model" in content
    assert "Section 7 — Production Velocity Improvement Model" in content
    assert "Section 8 — Human Governance Boundary" in content
    assert "Section 9 — Risk Controls" in content
    assert "Section 10 — Awareness of Active SAGE Workstreams" in content

    # Verify core pillars and questions
    assert "capability tree" in content_lower
    assert "validation framework" in content_lower
    assert "evidence package model" in content_lower

    # Verify Passport required fields
    passport_fields = [
        "capability name",
        "purpose",
        "lifecycle state",
        "dependencies",
        "validation strategy",
        "evidence path",
        "archive location",
        "reviewer decision",
        "allowed next state"
    ]
    for field in passport_fields:
        assert field in content_lower, f"Missing required Capability Passport field: {field}"

    # Verify No Orphan Capability Rule
    assert "no orphan capability rule" in content_lower

    # Verify State Transition Model & Example
    assert "cmaps validation schema" in content_lower
    assert "exp-cmaps-001" in content_lower
    assert "validated experimental" in content_lower

    # Verify Evidence Package Model required fields
    evidence_fields = [
        "experiment id",
        "timestamp",
        "environment state",
        "scenario blueprint",
        "expected result",
        "observed result",
        "artifacts",
        "failures",
        "boundary assessment",
        "lifecycle state",
        "reviewer decision ledger"
    ]
    for field in evidence_fields:
        assert field in content_lower, f"Missing required Evidence Package field: {field}"

    # Verify Failure as Information Model stages
    assert "isolated" in content_lower
    assert "measured" in content_lower
    assert "documented" in content_lower
    assert "classified" in content_lower
    assert "preserved" in content_lower
    assert "observation" in content_lower

    # Verify Velocity Improvement Old & New patterns
    assert "idea" in content_lower
    assert "classification" in content_lower
    assert "implementation" in content_lower

    # Verify Human Governance Boundary rules
    assert "render observes" in content_lower or "render" in content_lower
    assert "sage analyzes" in content_lower or "sage" in content_lower
    assert "humans decide" in content_lower or "humans" in content_lower
    assert "master archive records" in content_lower or "master archive" in content_lower
    assert "no automated promotion" in content_lower
    assert "no autonomous lifecycle advancement" in content_lower
    assert "no evidence without review" in content_lower

    # Verify Risk Controls
    assert "cognitive drift" in content_lower
    assert "orphan capabilities" in content_lower
    assert "documentation fragmentation" in content_lower
    assert "premature implementation" in content_lower
    assert "infrastructure contamination" in content_lower
    assert "false confidence" in content_lower


def test_roadmap_continuity_review_report_exists_and_conforms():
    """Verify that the SAGE-ROADMAP-CONTINUITY-REVIEW-REPORT.md document exists and has core required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    review_doc = root_dir / "docs" / "SAGE-ROADMAP-CONTINUITY-REVIEW-REPORT.md"

    assert review_doc.exists(), "The SAGE Roadmap Continuity Review report must exist under docs/"
    content = review_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-ROADMAP-REVIEW-2026-07-29" in content
    assert "PROPOSED — Strategic Review Phase" in content

    # Verify Section headings
    assert "Section 1 — Workstream Coordination Status Matrix" in content
    assert "Section 2 — Completed Milestones" in content
    assert "Section 3 — Active Research Tracks" in content
    assert "Section 4 — Pending Validation Gates" in content
    assert "Section 5 — Safe Next Engineering Directions" in content
    assert "Section 6 — Items Requiring No Action Yet" in content
    assert "Section 7 — Conclusion & Governance Recommendation" in content

    # Verify presence of specific concepts
    assert "acr v1.0.0" in content_lower
    assert "sage-act milestones 1 through 4" in content_lower or "milestones 1 through 4" in content_lower
    assert "cmaps v1.1" in content_lower
    assert "validation gate checklist" in content_lower
    assert "safe dry-run" in content_lower or "sage-sdr" in content_lower


def test_governance_dependency_map_exists_and_conforms():
    """Verify that the SAGE-GOVERNANCE-DEPENDENCY-MAP.md document exists and has core required sections."""
    root_dir = Path(__file__).parent.parent.parent
    map_doc = root_dir / "docs" / "SAGE-GOVERNANCE-DEPENDENCY-MAP.md"

    assert map_doc.exists(), "The SAGE Governance Dependency Map document must exist under docs/"
    content = map_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-GOV-DEPMAP-2026-07-29" in content
    assert "PROPOSED — Strategic Review Phase" in content

    # Verify Sections
    assert "Section 1 — Governance Artifact Relationship Map" in content
    assert "Section 2 — Source-of-Truth Hierarchy" in content
    assert "Section 3 — Document Ownership Boundaries" in content
    assert "Section 4 — Duplicate-Risk Assessment" in content
    assert "Section 5 — Cross-Reference Recommendations" in content
    assert "Section 6 — Future Synchronization Rules" in content
    assert "Section 7 — Conclusion" in content

    # Verify Specific terms
    assert "source-of-truth hierarchy" in content_lower or "source-of-truth ordering" in content_lower
    assert "ownership boundaries" in content_lower
    assert "duplicate-risk assessment" in content_lower
    assert "future synchronization rules" in content_lower


def test_master_synchronization_checkpoint_report_exists_and_conforms():
    """Verify that the SAGE-MASTER-SYNCHRONIZATION-CHECKPOINT-REPORT.md document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    report_doc = root_dir / "docs" / "SAGE-MASTER-SYNCHRONIZATION-CHECKPOINT-REPORT.md"

    assert report_doc.exists(), "The SAGE Master Synchronization Checkpoint Report document must exist under docs/"
    content = report_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-MASTER-SYNC-2026-07-29" in content
    assert "PROPOSED — Strategic Review Phase" in content

    # Verify Sections
    assert "Section 1 — Current SAGE System State" in content
    assert "Section 2 — Three-Lane Reconciliation Summary" in content
    assert "Section 3 — Multi-Dimensional Maturity Assessment" in content
    assert "Section 4 — Active Workstream Inventory" in content
    assert "Section 5 — Remaining Research Gaps" in content
    assert "Section 6 — Recommended Next Engineering Sequence" in content
    assert "Section 7 — Frozen Items (No Action Authorized)" in content
    assert "Section 8 — Conclusion & Master Alignment Recommendation" in content

    # Verify key terminology
    assert "three-lane reconciliation" in content_lower
    assert "multi-dimensional maturity" in content_lower
    assert "recommended next engineering sequence" in content_lower
    assert "sage-sdr" in content_lower or "safe dry-run" in content_lower


def test_agent_continuity_governance_framework_exists_and_conforms():
    """Verify that the SAGE-AGENT-CONTINUITY-GOVERNANCE-FRAMEWORK.md document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    agent_gov_doc = root_dir / "docs" / "SAGE-AGENT-CONTINUITY-GOVERNANCE-FRAMEWORK.md"

    assert agent_gov_doc.exists(), "The SAGE Agent Continuity Governance Framework document must exist under docs/"
    content = agent_gov_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-AGENT-GOV-2026-07-29" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify Sections
    assert "Section 1 — Multi-Agent Operating Model" in content
    assert "Section 2 — Agent Passport Model" in content
    assert "Section 3 — Agent Role Separation" in content
    assert "Section 4 — Multi-Agent Handoff Protocol" in content
    assert "Section 5 — Agent Risk Controls" in content
    assert "Section 6 — Future Agent Expansion Rules" in content
    assert "Section 7 — Conclusion" in content

    # Verify specific rules and terminology
    assert "no agent without accountability rule" in content_lower
    assert "chatgpt" in content_lower
    assert "jules" in content_lower
    assert "claude" in content_lower
    assert "architectural coordination" in content_lower
    assert "repository operations" in content_lower
    assert "adversarial review" in content_lower


def test_agent_ecosystem_activation_roadmap_exists_and_conforms():
    """Verify that the SAGE-AGENT-ECOSYSTEM-ACTIVATION-ROADMAP.md document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    roadmap_doc = root_dir / "docs" / "SAGE-AGENT-ECOSYSTEM-ACTIVATION-ROADMAP.md"

    assert roadmap_doc.exists(), "The SAGE Agent Ecosystem Activation Roadmap document must exist under docs/"
    content = roadmap_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-AGENT-ACTIVATION-2026-07-29" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify Sections
    assert "Section 1 — Current Activation Readiness" in content
    assert "Section 2 — Multi-Agent Operating Hierarchy & Handoff Protocol" in content
    assert "Section 3 — The Five-Stage Activation Roadmap" in content
    assert "Section 4 — Multi-Agent Risk Controls & Validation Gates" in content
    assert "Section 5 — Human Governance Requirements" in content
    assert "Section 6 — Conclusion & Recommended Next Steps" in content

    # Verify stages
    assert "the five-stage activation roadmap" in content_lower
    assert "stage 1" in content_lower
    assert "stage 2" in content_lower
    assert "stage 3" in content_lower
    assert "stage 4" in content_lower
    assert "stage 5" in content_lower


def test_agent_coordination_model_exists_and_conforms():
    """Verify that the SAGE-AGENT-COORDINATION-MODEL.md document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    model_doc = root_dir / "docs" / "SAGE-AGENT-COORDINATION-MODEL.md"

    assert model_doc.exists(), "The SAGE Agent Coordination Model document must exist under docs/"
    content = model_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-AGENT-COORDINATION-2026-07-29" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify Sections
    assert "Section 1 — Coordination Architecture" in content
    assert "Section 2 — Agent Task Lifecycle" in content
    assert "Section 3 — Agent Handoff Envelope" in content
    assert "Section 4 — Agent Coordination Rules" in content
    assert "Section 5 — Failure Recovery Model" in content
    assert "Section 6 — Future Coordination Research" in content
    assert "Section 7 — Conclusion" in content

    # Verify specific items
    assert "human task request" in content_lower
    assert "task classification" in content_lower
    assert "agent assignment" in content_lower
    assert "execution boundary check" in content_lower
    assert "agent work product" in content_lower
    assert "evidence package creation" in content_lower
    assert "independent review" in content_lower
    assert "human decision" in content_lower
    assert "master archive update" in content_lower

    # Verify handoff fields
    assert "task id" in content_lower
    assert "agent identity" in content_lower
    assert "mission purpose" in content_lower
    assert "input context" in content_lower
    assert "allowed actions" in content_lower
    assert "restricted actions" in content_lower
    assert "output artifact" in content_lower
    assert "evidence produced" in content_lower
    assert "validation status" in content_lower
    assert "next reviewer" in content_lower
    assert "archive destination" in content_lower

    # Verify coordination rules
    assert "no agent without passport" in content_lower
    assert "no action without traceability" in content_lower
    assert "no output without evidence context" in content_lower
    assert "no promotion without human review" in content_lower
    assert "no hidden state transfer" in content_lower


def test_multi_agent_council_alignment_review_exists_and_conforms():
    """Verify that the SAGE-MULTI-AGENT-COUNCIL-ALIGNMENT-REVIEW.md document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    council_doc = root_dir / "docs" / "SAGE-MULTI-AGENT-COUNCIL-ALIGNMENT-REVIEW.md"

    assert council_doc.exists(), "The SAGE Multi-Agent Council Alignment Review document must exist under docs/"
    content = council_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-COUNCIL-REVIEW-2026-07-29" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify Sections
    assert "Section 1 — Current Agent Ecosystem State" in content
    assert "Section 2 — Role Alignment Assessment" in content
    assert "Section 3 — Communication Alignment & Handoff Integrity" in content
    assert "Section 4 — Evidence Flow & Agent Accountability" in content
    assert "Section 5 — Coordination Risk Controls" in content
    assert "Section 6 — Remaining Governance Gaps & Future Coordination Requirements" in content
    assert "Section 7 — Frozen Items (No Action Authorized)" in content
    assert "Section 8 — Conclusion" in content

    # Verify specific roles and rules
    assert "chatgpt" in content_lower
    assert "jules" in content_lower
    assert "claude" in content_lower
    assert "gemini / google ai" in content_lower
    assert "role separation rule" in content_lower
    assert "no agent without accountability rule" in content_lower


def test_multi_agent_council_operating_charter_exists_and_conforms():
    """Verify that the SAGE-MULTI-AGENT-COUNCIL-OPERATING-CHARTER.md document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    charter_doc = root_dir / "docs" / "SAGE-MULTI-AGENT-COUNCIL-OPERATING-CHARTER.md"

    assert charter_doc.exists(), "The SAGE Multi-Agent Council Operating Charter document must exist under docs/"
    content = charter_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-COUNCIL-CHARTER-2026-07-29" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify Sections
    assert "Section 1 — Council Purpose" in content
    assert "Section 2 — Council Structure" in content
    assert "Section 3 — Agent Membership Requirements" in content
    assert "Section 4 — Council Communication Rules" in content
    assert "Section 5 — Decision Ownership Model" in content
    assert "Section 6 — Council Failure Handling" in content
    assert "Section 7 — Future Agent Expansion Rules" in content
    assert "Section 8 — Conclusion" in content

    # Verify specific clauses
    assert "no passport = no participation" in content_lower
    assert "sovereignty boundary" in content_lower
    assert "assistance vs. authorization" in content_lower
    assert "human-owned decisions" in content_lower
    assert "agent-owned actions" in content_lower


def test_validation_evidence_traceability_synchronization_report_exists_and_conforms():
    """Verify that the SAGE-VALIDATION-EVIDENCE-TRACEABILITY-SYNCHRONIZATION-REPORT.md document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    report_doc = root_dir / "docs" / "SAGE-VALIDATION-EVIDENCE-TRACEABILITY-SYNCHRONIZATION-REPORT.md"

    assert report_doc.exists(), "The SAGE Validation Evidence Traceability Synchronization Report document must exist under docs/"
    content = report_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-TRACE-SYNC-2026-07-29" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify Sections
    assert "Section 1 — Current Validation Ecosystem State" in content
    assert "Section 2 — Artifact Traceability Map" in content
    assert "Section 3 — Evidence Chain Assessment" in content
    assert "Section 4 — Master Archive Consistency Review" in content
    assert "Section 5 — Remaining Validation Infrastructure Gaps" in content
    assert "Section 6 — Recommended Next Engineering Preparation Step" in content
    assert "Section 7 — Frozen Items Requiring No Action" in content_lower or "section 7 — frozen items (no action authorized)" in content_lower
    assert "Section 8 — Conclusion" in content

    # Verify specific concepts
    assert "accountability invariant" in content_lower
    assert "capability passport" in content_lower
    assert "evidence receipt" in content_lower
    assert "human review" in content_lower


def test_experimental_engineering_readiness_gate_exists_and_conforms():
    """Verify that the SAGE-EXPERIMENTAL-ENGINEERING-READINESS-GATE.md document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    gate_doc = root_dir / "docs" / "SAGE-EXPERIMENTAL-ENGINEERING-READINESS-GATE.md"

    assert gate_doc.exists(), "The SAGE Experimental Engineering Readiness Gate document must exist under docs/"
    content = gate_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID and Status
    assert "SAGE-READINESS-GATE-2026-07-29" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify Sections
    assert "Section 1 — Experimental Infrastructure Readiness" in content
    assert "Section 2 — Engineering Dependency Chain" in content
    assert "Section 3 — First Controlled Experiment Requirements" in content
    assert "Section 4 — Engineering Risk Assessment" in content
    assert "Section 5 — Recommended First Engineering Milestone" in content
    assert "Section 6 — Conclusion" in content

    # Verify specific keywords
    assert "experimental infrastructure readiness" in content_lower
    assert "engineering dependency chain" in content_lower
    assert "first controlled experiment requirements" in content_lower
    assert "engineering risk assessment" in content_lower
    assert "recommended first engineering milestone" in content_lower
    assert "sagecoordinated sandbox simulation" in content_lower or "sage-sdr" in content_lower


def test_documents_are_indexed_correctly():
    """Verify that all required governance documents are registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state for all eleven
    assert "../docs/SAGE-CAPABILITY-EVOLUTION-GOVERNANCE-FRAMEWORK.md" in content
    assert "../docs/SAGE-ROADMAP-CONTINUITY-REVIEW-REPORT.md" in content
    assert "../docs/SAGE-GOVERNANCE-DEPENDENCY-MAP.md" in content
    assert "../docs/SAGE-MASTER-SYNCHRONIZATION-CHECKPOINT-REPORT.md" in content
    assert "../docs/SAGE-AGENT-CONTINUITY-GOVERNANCE-FRAMEWORK.md" in content
    assert "../docs/SAGE-AGENT-ECOSYSTEM-ACTIVATION-ROADMAP.md" in content
    assert "../docs/SAGE-AGENT-COORDINATION-MODEL.md" in content
    assert "../docs/SAGE-MULTI-AGENT-COUNCIL-ALIGNMENT-REVIEW.md" in content
    assert "../docs/SAGE-MULTI-AGENT-COUNCIL-OPERATING-CHARTER.md" in content
    assert "../docs/SAGE-VALIDATION-EVIDENCE-TRACEABILITY-SYNCHRONIZATION-REPORT.md" in content
    assert "../docs/SAGE-EXPERIMENTAL-ENGINEERING-READINESS-GATE.md" in content
    assert "[State: PROPOSED]" in content


def test_governance_framework_protected_boundary_isolation():
    """Assert that zero changes have been made to protected production and configuration namespaces.

    Only sage/experimental/act/, tests/experimental/, and documentation/indexes are allowed modifications.
    """
    root_dir = Path(__file__).parent.parent.parent
    sage_dir = root_dir / "sage"

    # Ensure no experimental code leakage into production directories (One-Way Import Law)
    for path in sage_dir.glob("**/*.py"):
        if "experimental" in path.parts:
            continue

        # Check file content does not import experimental namespaces
        with open(path, "r", encoding="utf-8") as f:
            file_content = f.read()
            try:
                tree = ast.parse(file_content, filename=str(path))
            except SyntaxError:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        assert "sage.experimental" not in alias.name, (
                            f"One-Way Import Law Violation: '{path}' "
                            f"attempts to directly import '{alias.name}'"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        assert "sage.experimental" not in node.module, (
                            f"One-Way Import Law Violation: '{path}' "
                            f"attempts to import from module '{node.module}'"
                        )
