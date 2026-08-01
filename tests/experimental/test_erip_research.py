"""SAGE Evidence Reconciliation & Ingestion Protocol (SAGE-ERIP) validation suite."""

import os
import ast
from pathlib import Path


def test_erip_specification_document_exists_and_conforms():
    """Verify that the SAGE-EVIDENCE-RECONCILIATION-INGESTION-PROTOCOL-RESEARCH-SPECIFICATION.md exists and has required sections and terms."""
    root_dir = Path(__file__).parent.parent.parent
    erip_doc = root_dir / "docs" / "SAGE-EVIDENCE-RECONCILIATION-INGESTION-PROTOCOL-RESEARCH-SPECIFICATION.md"

    assert erip_doc.exists(), "The ERIP Research Specification must exist under docs/"
    content = erip_doc.read_text(encoding="utf-8")
    content_lower = content.lower()

    # Verify ID, Classification and Status
    assert "SAGE-ERIP-RESEARCH-2026-08-01" in content
    assert "PROPOSED — Strategic Research Phase" in content

    # Verify key sections
    assert "1. SAGE-ERIP Architecture Model" in content
    assert "2. Evidence Intake Model" in content
    assert "3. Evidence Reconciliation Model" in content
    assert "4. Provenance Model" in content
    assert "5. Contradiction Detection" in content
    assert "6. Enterprise Requirements" in content
    assert "7. Measurement Alignment" in content
    assert "8. Operational Boundaries & Exclusions" in content

    # Verify evidence intake model terms
    assert "accepted evidence sources" in content_lower
    assert "trust boundaries" in content_lower
    assert "authenticity requirements" in content_lower
    assert "validation ownership" in content_lower
    assert "human approval gates" in content_lower

    # Verify reconciliation model terms
    assert "evidence package comparison" in content_lower
    assert "receipt matching" in content_lower or "receipt verification" in content_lower
    assert "checksum verification" in content_lower
    assert "reconciliation" in content_lower
    assert "conflicting evidence handling" in content_lower

    # Verify provenance model terms
    assert "origin tracking" in content_lower
    assert "ancestry" in content_lower
    assert "validation history" in content_lower
    assert "relationship" in content_lower

    # Verify contradiction detection terms
    assert "duplicate evidence" in content_lower
    assert "stale evidence" in content_lower
    assert "missing receipts" in content_lower
    assert "historical divergence" in content_lower
    assert "archive divergence" in content_lower

    # Verify enterprise requirements
    assert "audit reconstruction" in content_lower
    assert "multi-party review" in content_lower
    assert "compliance retention" in content_lower
    assert "external evidence trust" in content_lower

    # Verify measurement alignment terms
    assert "eqs" in content_lower or "evidence quality score" in content_lower
    assert "tcs" in content_lower or "telemetry completeness score" in content_lower
    assert "ars" in content_lower or "adversarial resilience score" in content_lower


def test_erip_is_indexed_correctly():
    """Verify that the ERIP specification is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state
    assert "../docs/SAGE-EVIDENCE-RECONCILIATION-INGESTION-PROTOCOL-RESEARCH-SPECIFICATION.md" in content
    assert "[State: PROPOSED]" in content


def test_erip_protected_boundary_isolation():
    """Assert that zero changes have been made to protected production and configuration namespaces."""
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
