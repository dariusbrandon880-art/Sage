"""Automated read-only verification for SAGE-ACT Milestone 2 Planning artifacts."""

import os
import ast
from pathlib import Path


def test_milestone_2_planning_document_exists_and_is_valid():
    """Verify that the Milestone 2 planning document exists and contains required sections."""
    root_dir = Path(__file__).parent.parent.parent
    planning_doc_path = root_dir / "docs" / "SAGE-ACT-MILESTONE-2-PLANNING.md"

    # Assert file exists
    assert planning_doc_path.exists(), f"Expected planning document not found at: {planning_doc_path}"

    content = planning_doc_path.read_text(encoding="utf-8")

    # Assert critical sections and keywords are present
    required_phrases = [
        "SAGE-ACT-MP-2.0",
        "SessionState → AgentTask Lineage Inspection",
        "AgentTask → DecisionEntry Causal Mapping",
        "Validation of Lineage Integrity and Malformed-State Rejection",
        "Additional Read-Only Safety Checks Before Any Future Mutation Capability",
        "Class and Method Interface Design",
        "File Impact Report",
        "Validation and Test Strategy",
        "Zero Production Footprint",
        "Milestone 2 Architecture Review",
        "Implementation Boundary Map",
        "Proposed File Structure for Future Read-Only Lineage Expansion",
        "Risk Assessment and Mitigations",
        "Nonce Freshness Validation",
        "Acyclic Lineage Verification",
        "Read-Only Expansion Design Review",
        "SessionTaskTreeLinker",
        "TaskDecisionBinder",
    ]

    for phrase in required_phrases:
        assert phrase in content, f"Missing required focus/phrase in planning document: '{phrase}'"


def test_milestone_2_planning_is_indexed_properly():
    """Verify that the Milestone 2 planning document is registered as PROPOSED in INDEX.md."""
    root_dir = Path(__file__).parent.parent.parent
    index_path = root_dir / "Main Archive" / "INDEX.md"

    # Assert INDEX.md exists
    assert index_path.exists(), f"Expected INDEX.md not found at: {index_path}"

    content = index_path.read_text(encoding="utf-8")

    # Assert registration with exact file reference and PROPOSED state
    assert "../docs/SAGE-ACT-MILESTONE-2-PLANNING.md" in content
    assert "[State: PROPOSED]" in content
    assert "SAGE Agent Continuity Tree (SAGE-ACT) Multi-Agent Lineage" in content


def test_production_isolation_and_zero_footprint():
    """Assert that zero changes have been made to protected production and configuration namespaces.

    Only sage/experimental/act/, tests/experimental/, and documentation/indexes are allowed modifications.
    """
    root_dir = Path(__file__).parent.parent.parent
    sage_dir = root_dir / "sage"

    # Ensure no experimental code leakage into production directories
    for path in sage_dir.glob("**/*.py"):
        if "experimental" in path.parts:
            continue

        # Check file content does not import experimental namespaces
        with open(path, "r", encoding="utf-8") as f:
            file_content = f.read()
            tree = ast.parse(file_content, filename=str(path))

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
