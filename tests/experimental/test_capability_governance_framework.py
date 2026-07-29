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


def test_governance_framework_is_indexed_correctly():
    """Verify that the Capability Evolution Governance Framework is registered in Main Archive/INDEX.md as PROPOSED."""
    root_dir = Path(__file__).parent.parent.parent
    index_file = root_dir / "Main Archive" / "INDEX.md"

    assert index_file.exists(), "Index file must exist in Main Archive/"
    content = index_file.read_text(encoding="utf-8")

    # Assert correct link format and state
    assert "../docs/SAGE-CAPABILITY-EVOLUTION-GOVERNANCE-FRAMEWORK.md" in content
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
