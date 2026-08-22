"""Tests for evidence closure."""

from pathlib import Path
from sage.capability_evidence import assess_evidence_closure
from sage.capability_registry import SAGECapability


def test_evidence_closure_detects_missing_artifacts(tmp_path):
    capability = SAGECapability(
        capability_id="CAP-TEST-EVIDENCE",
        name="Evidence Test",
        description="test",
        evidence_references=["evidence.json"],
        test_references=["tests/test_evidence.py"],
    )
    (tmp_path / "evidence.json").write_text("{}", encoding="utf-8")

    closure = assess_evidence_closure(capability, str(tmp_path))
    assert closure.missing_evidence == []
    assert closure.missing_tests == ["tests/test_evidence.py"]
    assert closure.closed is False


def test_evidence_closure_closes_when_all_artifacts_exist(tmp_path):
    capability = SAGECapability(
        capability_id="CAP-TEST-EVIDENCE",
        name="Evidence Test",
        description="test",
        evidence_references=["evidence.json"],
        test_references=["tests/test_evidence.py"],
    )
    (tmp_path / "evidence.json").write_text("{}", encoding="utf-8")
    Path(tmp_path / "tests").mkdir()
    (tmp_path / "tests/test_evidence.py").write_text("", encoding="utf-8")

    assert assess_evidence_closure(capability, str(tmp_path)).closed is True
