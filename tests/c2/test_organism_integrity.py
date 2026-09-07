"""Adversarial tests for whole-organism structural integrity."""

from pathlib import Path

import pytest

from sage.c2.organism_integrity import (
    assert_organism_integrity,
    evaluate_organism_integrity,
)
from sage.c2.organism_jigsaw import JigsawRelationship, SubsystemRegistration


HEAD = "589deed62566f31bc5a2700deb142cc3b3433d79"


def _catalog(*registrations: SubsystemRegistration) -> list[SubsystemRegistration]:
    return list(registrations)


def test_actual_repository_inventory_is_not_empty():
    report = evaluate_organism_integrity(HEAD)
    assert report.exact_git_head == HEAD
    assert report.discovered_modules
    assert "sage/c2/organism_integrity.py" in report.discovered_modules


def test_undeclared_organ_is_detected(tmp_path: Path):
    organ = tmp_path / "sage" / "new_organ.py"
    organ.parent.mkdir(parents=True)
    organ.write_text("def execute():\n    return True\n", encoding="utf-8")

    report = evaluate_organism_integrity(
        HEAD,
        root_dir=str(tmp_path),
        catalog=[],
    )
    assert any(f.kind == "UNDECLARED_ORGAN" and f.subject == "sage/new_organ.py" for f in report.findings)


def test_missing_organ_is_detected(tmp_path: Path):
    (tmp_path / "sage").mkdir()
    catalog = _catalog(
        SubsystemRegistration(
            subsystem_id="missing",
            module_path="sage/missing.py",
            relationship=JigsawRelationship.CORE,
            description="missing organ",
        )
    )
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert any(f.kind == "MISSING_ORGAN" and f.subject == "sage/missing.py" for f in report.findings)


def test_projection_filesystem_mutation_is_detected(tmp_path: Path):
    organ = tmp_path / "sage" / "projection.py"
    organ.parent.mkdir(parents=True)
    organ.write_text(
        "from pathlib import Path\n"
        "def render():\n"
        "    Path('state.txt').write_text('bad')\n",
        encoding="utf-8",
    )
    catalog = _catalog(
        SubsystemRegistration(
            subsystem_id="projection",
            module_path="sage/projection.py",
            relationship=JigsawRelationship.PROJECTION,
            description="projection",
        )
    )
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert any(f.kind == "PROJECTION_MUTATION_SURFACE" for f in report.findings)


def test_integrity_assertion_fails_closed(tmp_path: Path):
    (tmp_path / "sage").mkdir()
    (tmp_path / "sage" / "orphan.py").write_text("VALUE = 1\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="UNDECLARED_ORGAN"):
        assert_organism_integrity(HEAD, root_dir=str(tmp_path))


def test_digest_is_deterministic(tmp_path: Path):
    (tmp_path / "sage").mkdir()
    (tmp_path / "sage" / "orphan.py").write_text("VALUE = 1\n", encoding="utf-8")
    first = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path))
    second = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path))
    assert first.digest == second.digest
    assert first.findings == second.findings
