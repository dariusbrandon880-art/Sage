from sage.capability_lineage import project_capability_lineage
from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry


def registry_with(cap):
    registry = SAGEOperationalCapabilityRegistry.__new__(SAGEOperationalCapabilityRegistry)
    registry.capabilities = {cap.capability_id: cap}
    return registry


def test_missing_evidence_is_stale_without_mutation(tmp_path):
    cap = SAGECapability(capability_id="CAP-X", name="X", description="x", evidence_references=["evidence/missing.json"], test_references=[])
    projection = project_capability_lineage(registry_with(cap), tmp_path)
    assert projection.capabilities[0].effective_lifecycle == "STALE_EVIDENCE"
    assert cap.validation_status == "VALIDATED"


def test_complete_surface_is_validated(tmp_path):
    (tmp_path / "evidence").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "evidence/e.json").write_text("{}")
    (tmp_path / "tests/t.py").write_text("")
    cap = SAGECapability(capability_id="CAP-X", name="X", description="x", evidence_references=["evidence/e.json"], test_references=["tests/t.py"])
    projection = project_capability_lineage(registry_with(cap), tmp_path)
    assert projection.capabilities[0].effective_lifecycle == "VALIDATED"
