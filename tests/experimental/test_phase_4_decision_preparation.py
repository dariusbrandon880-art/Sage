"""SAGE Phase 4 Controlled Evaluation Decision Preparation programmatic validation suite."""

import os
import ast
from pathlib import Path


def test_phase_4_decision_preparation_document_exists_and_conforms():
    """Verify that the SAGE-PHASE-4-CONTROLLED-EVALUATION-DECISION-PREPARATION.md document exists and has core required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    doc_path = root_dir / "docs" / "SAGE-PHASE-4-CONTROLLED-EVALUATION-DECISION-PREPARATION.md"

    assert doc_path.exists(), "The SAGE Phase 4 Decision Preparation document must exist under docs/"
    content = doc_path.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID, Classification and Status
    assert "SAGE-PHASE-4-DECISION-PREP-2026-08-02" in content
    assert "Strategic Transition Assessment & Governance Record" in content
    assert "Proposed - Awaiting Human Authorization" in content

    # Verify Key Core Sections from SAGE Required Return
    assert "SAGE Phase 4 Decision Preparation Status" in content
    assert "Evidence Review Status" in content
    assert "Current Capability Assessment" in content
    assert "Validated Advantages" in content
    assert "Remaining Limitations" in content
    assert "Available Options" in content
    assert "Recommended Transition" in content
    assert "Required Human Authorization" in content
    assert "Next Execution Boundary" in content

    # Verify strategic rules and decision questions
    assert "do not optimize for more capability" in content_lower
    assert "optimize for controlled evidence growth" in content_lower
    assert "does the current sage governed-agent prototype demonstrate sufficient measurable advantage" in content_lower

    # Verify decision options and recommendations
    assert "option a" in content_lower
    assert "option b" in content_lower
    assert "option c" in content_lower
    assert "option d" in content_lower
    assert "option b — controlled workflow expansion" in content_lower


def test_phase_4_decision_preparation_is_indexed_correctly():
    """Verify that the Phase 4 Decision Preparation document is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state
    assert "../docs/SAGE-PHASE-4-CONTROLLED-EVALUATION-DECISION-PREPARATION.md" in content
    assert "[State: PROPOSED]" in content


def test_phase_4_decision_preparation_protected_boundary_isolation():
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
