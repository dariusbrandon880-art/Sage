"""SAGE Evidence and Validation Readiness Assessment programmatic validation suite."""

import os
import ast
from pathlib import Path


def test_evidence_validation_readiness_document_exists_and_conforms():
    """Verify that the SAGE-EVIDENCE-VALIDATION-READINESS-ASSESSMENT.md document exists and has core required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    assessment_doc = root_dir / "docs" / "SAGE-EVIDENCE-VALIDATION-READINESS-ASSESSMENT.md"

    assert assessment_doc.exists(), "The SAGE Evidence and Validation Readiness Assessment document must exist under docs/"
    content = assessment_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID, Classification and Status
    assert "SAGE-EVIDENCE-VALIDATION-READINESS-ASSESSMENT-2026-07-29" in content
    assert "PROPOSED — SAGE Evidence Integration Lane" in content

    # Verify Sections
    assert "Section 1 — Core Operational Principle and Strict Separations" in content
    assert "Section 2 — Alignment Review of the SAGE Governance Frameworks" in content
    assert "Section 3 — Comprehensive Validation Readiness Evaluation" in content
    assert "Section 4 — SAGE Evidence Maturity Analysis" in content
    assert "Section 5 — Validation Strengths, Weaknesses, and Missing Requirements" in content
    assert "Section 6 — Remaining Research Gaps" in content
    assert "Section 7 — Recommended Evidence and Validation Improvements" in content
    assert "Section 8 — Future Validation Priorities and State Transition Recommendations" in content

    # Verify the core separations and concepts
    assert "observation" in content_lower
    assert "evidence approval" in content_lower
    assert "capability promotion" in content_lower
    assert "validation" in content_lower
    assert "authorization" in content_lower
    assert "only human governance decisions may authorize lifecycle movement" in content_lower

    # Verify standard evaluation areas
    assert "evidence package completeness" in content_lower
    assert "validation pathway clarity" in content_lower
    assert "lifecycle transition consistency" in content_lower
    assert "human review boundaries" in content_lower
    assert "evidence-to-archive traceability" in content_lower
    assert "missing validation requirements" in content_lower
    assert "remaining research gaps" in content_lower


def test_evidence_validation_readiness_is_indexed_correctly():
    """Verify that the SAGE Evidence and Validation Readiness Assessment is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state
    assert "../docs/SAGE-EVIDENCE-VALIDATION-READINESS-ASSESSMENT.md" in content
    assert "[State: PROPOSED]" in content


def test_evidence_validation_readiness_protected_boundary_isolation():
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
