from sage.capability_lineage import project_capability_lineage
from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry


def registry_with(*capabilities):
    registry = SAGEOperationalCapabilityRegistry.__new__(SAGEOperationalCapabilityRegistry)
    registry.capabilities = {cap.capability_id: cap for cap in capabilities}
    return registry


def test_projection_marks_missing_evidence_stale_without_mutation(tmp_path):
    cap = SAGECapability(
        capability_id="CAP-TEST",
        name="Test",
        description="test",
        evidence_references=["evidence/valid.json", "evidence/missing.json"],
        test_references=["tests/test_valid.py"],
    )
    (tmp_path / "evidence").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "evidence/valid.json").write_text("{}")
    (tmp_path / "tests/test_valid.py").write_text("")
    registry = registry_with(cap)

    projection = project_capability_lineage(registry, tmp_path)

    record = projection.capabilities[0]
    assert record.effective_lifecycle == "STALE_EVIDENCE"
    assert record.missing_evidence == ["evidence/missing.json"]
    assert registry.get_capability("CAP-TEST").validation_status == "VALIDATED"


def test_projection_marks_missing_test_stale(tmp_path):
    cap = SAGECapability(
        capability_id="CAP-TEST",
        name="Test",
        description="test",
        evidence_references=["evidence/valid.json"],
        test_references=["tests/missing_test.py"],
    )
    (tmp_path / "evidence").mkdir()
    (tmp_path / "evidence/valid.json").write_text("{}")

    record = project_capability_lineage(registry_with(cap), tmp_path).capabilities[0]
    assert record.effective_lifecycle == "STALE_TEST"
    assert record.missing_tests == ["tests/missing_test.py"]


def test_projection_validates_complete_surface(tmp_path):
    cap = SAGECapability(
        capability_id="CAP-TEST",
        name="Test",
        description="test",
        evidence_references=["evidence/valid.json"],
        test_references=["tests/test_valid.py"],
    )
    (tmp_path / "evidence").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "evidence/valid.json").write_text("{}")
    (tmp_path / "tests/test_valid.py").write_text("")

    projection = project_capability_lineage(registry_with(cap), tmp_path)
    assert projection.capabilities[0].effective_lifecycle == "VALIDATED"
    assert projection.stale_count == 0
