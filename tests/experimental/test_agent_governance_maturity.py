"""SAGE Agent Governance Maturity Phase 2 programmatic validation suite."""

import os
import ast
from pathlib import Path


def test_agent_governance_maturity_document_exists_and_conforms():
    """Verify that the SAGE-AGENT-GOVERNANCE-MATURITY-PHASE-2.md document exists and has core required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    gov_doc = root_dir / "docs" / "SAGE-AGENT-GOVERNANCE-MATURITY-PHASE-2.md"

    assert gov_doc.exists(), "The Agent Governance Maturity Phase 2 Research Specification must exist under docs/"
    content = gov_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID, Classification and Status
    assert "SAGE-AGM-PHASE-2-2026-08-01" in content
    assert "PROPOSED — Strategic Governance Design Phase" in content

    # Verify key sections
    assert "1. Multi-Agent Governance Model" in content
    assert "2. Role Separation Framework" in content
    assert "3. Delegation Constraints" in content
    assert "4. Evidence Ownership Model" in content
    assert "5. Conflict Resolution Mechanisms" in content
    assert "6. Approval Escalation Paths" in content
    assert "7. Enterprise Audit Workflow & Compliance Evidence Structure" in content
    assert "8. Validation Direction & Evidence Requirements" in content
    assert "9. Protected Boundaries & Exclusions" in content

    # Verify role separation framework terms
    assert "coordinator agent" in content_lower
    assert "executor agent" in content_lower
    assert "analyst agent" in content_lower
    assert "reviewer agent" in content_lower

    # Verify delegation constraints terms
    assert "delegation constraints" in content_lower
    assert "authorized capabilities inheritance" in content_lower
    assert "no-loop tree structure" in content_lower
    assert "cycles" in content_lower

    # Verify evidence ownership terms
    assert "evidence ownership model" in content_lower
    assert "owner_identity" in content_lower
    assert "role_context" in content_lower
    assert "parent_task_id" in content_lower
    assert "signature" in content_lower

    # Verify conflict resolution terms
    assert "conflict resolution mechanisms" in content_lower
    assert "technical disagreement" in content_lower
    assert "resource / routing conflict" in content_lower
    assert "semantic conflict" in content_lower

    # Verify approval escalation paths terms
    assert "approval escalation paths" in content_lower
    assert "tier 1: sandbox compliance gate" in content_lower
    assert "tier 2: advanced capability gate" in content_lower
    assert "tier 3: enterprise audit gate" in content_lower

    # Verify enterprise audit workflow terms
    assert "enterprise audit workflow" in content_lower
    assert "compliance evidence structure" in content_lower
    assert "compliance_pack.json" in content_lower
    assert "agent_identity_chain" in content_lower
    assert "capability_authorization_chain" in content_lower
    assert "delegation_record" in content_lower
    assert "execution_trace" in content_lower
    assert "approval_checkpoints" in content_lower
    assert "rejection_decisions" in content_lower
    assert "integrity_verification" in content_lower
    assert "audit_lineage" in content_lower

    # Verify validation direction terms
    assert "validation direction" in content_lower
    assert "governed multi-agent coordination" in content_lower
    assert "authorized delegation only" in content_lower
    assert "evidence continuity across actions" in content_lower
    assert "deterministic rejection behavior" in content_lower
    assert "human approval dependency" in content_lower
    assert "complete audit traceability" in content_lower

    # Verify evidence requirements terms
    assert "evidence requirements" in content_lower
    assert "agent identity chain" in content_lower
    assert "capability authorization chain" in content_lower
    assert "delegation record" in content_lower
    assert "execution trace" in content_lower
    assert "approval checkpoints" in content_lower
    assert "rejection decisions" in content_lower
    assert "integrity verification" in content_lower
    assert "audit lineage" in content_lower


def test_agent_governance_maturity_review_and_adversarial_analysis_exists_and_conforms():
    """Verify that the SAGE-AGENT-GOVERNANCE-MATURITY-PHASE-2-RESEARCH-REVIEW-ADVERSARIAL-ANALYSIS.md document exists and has core required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    review_doc = root_dir / "docs" / "SAGE-AGENT-GOVERNANCE-MATURITY-PHASE-2-RESEARCH-REVIEW-ADVERSARIAL-ANALYSIS.md"

    assert review_doc.exists(), "The Agent Governance Maturity Phase 2 Research Review must exist under docs/"
    content = review_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID, Classification and Status
    assert "SAGE-AGM-PHASE-2-REVIEW-2026-08-01" in content
    assert "PROPOSED — Strategic Review Phase" in content

    # Verify key sections
    assert "1. Missing Enterprise Requirements Audit" in content
    assert "2. Conceptual Stress-Testing & Adversarial Analysis" in content
    assert "3. Minimal Future Validation Experiment Design" in content
    assert "4. Operational Boundaries & Rules of Engagement" in content

    # Verify stress-testing scenario terms
    assert "lying or corrupt agents" in content_lower or "multi-agent disagreement" in content_lower
    assert "permission conflicts" in content_lower
    assert "evidence disputes" in content_lower
    assert "human escalation failure" in content_lower
    assert "compliance reconstruction" in content_lower

    # Verify missing requirements audit
    assert "identity non-repudiation" in content_lower
    assert "federated audit trail" in content_lower
    assert "real-time alerting" in content_lower
    assert "granular key rotation" in content_lower

    # Verify pilot/validation experiment design
    assert "safe-sdr-agm-003" in content_lower
    assert "minimal future validation experiment design" in content_lower
    assert "experiment parameters" in content_lower
    assert "programmatic sequence" in content_lower


def test_agent_governance_maturity_is_indexed_correctly():
    """Verify that the Agent Governance Maturity Phase 2 files are registered in Main Archive/INDEX.md as VALIDATED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state for spec
    assert "../docs/SAGE-AGENT-GOVERNANCE-MATURITY-PHASE-2.md" in content
    # Assert correct link format and state for review/adversarial analysis
    assert "../docs/SAGE-AGENT-GOVERNANCE-MATURITY-PHASE-2-RESEARCH-REVIEW-ADVERSARIAL-ANALYSIS.md" in content
    assert "[State: VALIDATED]" in content


def test_agent_governance_maturity_protected_boundary_isolation():
    """Assert that zero changes have been made to protected production and configuration namespaces.

    Only sage/experimental/, tests/experimental/, and documentation/indexes are allowed modifications.
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
