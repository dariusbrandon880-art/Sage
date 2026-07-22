"""Tests for SAGE Validation and Evidence Lifecycle Layer."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from sage.validation import (
    EvidenceRecord,
    ValidationOutcome,
    LifecycleState,
    LifecycleManager,
    Verifier,
)


def test_evidence_record_creation():
    """Test creating structured EvidenceRecord objects."""
    evidence = EvidenceRecord(
        source="pytest",
        evidence_type="test_result",
        related_component="sage/archive",
        supporting_references=["tests/test_archive.py"],
        metadata={"coverage": 0.98},
    )

    assert evidence.id.startswith("evidence_")
    assert evidence.source == "pytest"
    assert evidence.evidence_type == "test_result"
    assert evidence.related_component == "sage/archive"
    assert "tests/test_archive.py" in evidence.supporting_references
    assert evidence.metadata == {"coverage": 0.98}
    assert isinstance(evidence.timestamp, datetime)


def test_validation_outcome_creation():
    """Test creating ValidationOutcome records."""
    outcome = ValidationOutcome(
        item_id="archive_123",
        validation_method="pytest_suite",
        result=True,
        confidence_impact=0.1,
        related_tests=["test_archive_initialization"],
        details={"passed_tests": 5, "failed_tests": 0},
    )

    assert outcome.id.startswith("val_rec_")
    assert outcome.item_id == "archive_123"
    assert outcome.validation_method == "pytest_suite"
    assert outcome.result is True
    assert outcome.confidence_impact == 0.1
    assert "test_archive_initialization" in outcome.related_tests
    assert outcome.details == {"passed_tests": 5, "failed_tests": 0}


def test_lifecycle_manager_transitions():
    """Test asset lifecycle state transitions and restriction boundaries."""
    mgr = LifecycleManager(item_id="asset_001")

    # Initial state is Proposed
    assert mgr.current_state == LifecycleState.PROPOSED
    assert len(mgr.history) == 0

    # Transition Proposed -> Under Review
    success = mgr.transition_to(LifecycleState.UNDER_REVIEW, actor="lead_dev", reason="Initiating review")
    assert success is True
    assert mgr.current_state == LifecycleState.UNDER_REVIEW
    assert len(mgr.history) == 1
    assert mgr.history[0].from_state == LifecycleState.PROPOSED
    assert mgr.history[0].to_state == LifecycleState.UNDER_REVIEW
    assert mgr.history[0].actor == "lead_dev"

    # Invalid transition Under Review -> Archived (must go to Validated or Proposed first)
    success = mgr.transition_to(LifecycleState.ARCHIVED)
    assert success is False
    assert mgr.current_state == LifecycleState.UNDER_REVIEW

    # Transition Under Review -> Validated
    success = mgr.transition_to(LifecycleState.VALIDATED, actor="verifier_bot")
    assert success is True
    assert mgr.current_state == LifecycleState.VALIDATED

    # Transition Validated -> Promoted
    success = mgr.transition_to(LifecycleState.PROMOTED)
    assert success is True
    assert mgr.current_state == LifecycleState.PROMOTED

    # Transition Promoted -> Archived
    success = mgr.transition_to(LifecycleState.ARCHIVED)
    assert success is True
    assert mgr.current_state == LifecycleState.ARCHIVED

    # Archived is a terminal state (cannot transition out)
    success = mgr.transition_to(LifecycleState.PROPOSED)
    assert success is False
    assert mgr.current_state == LifecycleState.ARCHIVED


def test_verifier_utilities():
    """Test the lightweight verifier interface for automated checks."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Test verification
        dummy_test_file = tmp_path / "test_dummy.py"
        outcome, evidence = Verifier.verify_test_suite(str(dummy_test_file))
        assert outcome.result is False  # file doesn't exist yet

        dummy_test_file.write_text("def test_dummy(): pass")
        outcome, evidence = Verifier.verify_test_suite(str(dummy_test_file))
        assert outcome.result is True
        assert outcome.confidence_impact == 0.15
        assert dummy_test_file.name in outcome.details["file_path"]
        assert str(dummy_test_file) in evidence.supporting_references

        # 2. Documentation verification
        dummy_doc_file = tmp_path / "README.md"
        outcome, evidence = Verifier.verify_documentation(str(dummy_doc_file))
        assert outcome.result is False  # file doesn't exist yet

        dummy_doc_file.write_text("# SAGE Project\n## Overview\nThis is a documentation file.")
        outcome, evidence = Verifier.verify_documentation(str(dummy_doc_file), expected_sections=["Overview"])
        assert outcome.result is True
        assert outcome.details["sections_found"] == {"Overview": True}

        outcome, evidence = Verifier.verify_documentation(str(dummy_doc_file), expected_sections=["Overview", "MissingSection"])
        assert outcome.result is False
        assert outcome.details["sections_found"] == {"Overview": True, "MissingSection": False}

        # 3. Architecture verification
        dummy_dir = tmp_path / "sage_architecture"
        outcome, evidence = Verifier.verify_architecture(str(dummy_dir), ["core.py", "api.py"])
        assert outcome.result is False  # directory doesn't exist

        dummy_dir.mkdir()
        (dummy_dir / "core.py").write_text("")
        outcome, evidence = Verifier.verify_architecture(str(dummy_dir), ["core.py", "api.py"])
        assert outcome.result is False  # api.py is missing
        assert outcome.details["missing_files"] == ["api.py"]

        (dummy_dir / "api.py").write_text("")
        outcome, evidence = Verifier.verify_architecture(str(dummy_dir), ["core.py", "api.py"])
        assert outcome.result is True
        assert len(outcome.details["missing_files"]) == 0
        assert len(evidence.supporting_references) == 2
