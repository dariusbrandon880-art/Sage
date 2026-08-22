import pytest
from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry
from sage.evidence_closure import check_evidence_closure, require_closed


def registry_with(cap):
    registry = SAGEOperationalCapabilityRegistry.__new__(SAGEOperationalCapabilityRegistry)
    registry.capabilities = {cap.capability_id: cap}
    return registry


def test_missing_artifact_blocks_closure(tmp_path):
    cap = SAGECapability(capability_id="CAP-X", name="X", description="x", evidence_references=["evidence/missing.json"], test_references=[])
    records = check_evidence_closure(registry_with(cap), tmp_path)
    assert not records[0].closed
    with pytest.raises(ValueError, match="EVIDENCE_CLOSURE_INCOMPLETE"):
        require_closed(records)


def test_complete_artifacts_close_cleanly(tmp_path):
    (tmp_path / "evidence").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "evidence/e.json").write_text("{}")
    (tmp_path / "tests/t.py").write_text("")
    cap = SAGECapability(capability_id="CAP-X", name="X", description="x", evidence_references=["evidence/e.json"], test_references=["tests/t.py"])
    records = check_evidence_closure(registry_with(cap), tmp_path)
    assert records[0].closed
    require_closed(records)
