"""Adversarial tests for whole-organism structural integrity."""

from pathlib import Path
import subprocess

import pytest

from sage.c2.organism_integrity import assert_organism_integrity, evaluate_organism_integrity
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
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=[])
    assert any(f.kind == "UNDECLARED_ORGAN" and f.subject == "sage/new_organ.py" for f in report.findings)


def test_registered_package_tree_is_one_organ(tmp_path: Path):
    package = tmp_path / "sage" / "c2"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "helper.py").write_text("VALUE = 2\n", encoding="utf-8")
    catalog = _catalog(SubsystemRegistration(
        subsystem_id="c2",
        module_path="sage/c2/",
        relationship=JigsawRelationship.CORE,
        description="C2 package boundary",
    ))
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert not any(f.kind == "UNDECLARED_ORGAN" for f in report.findings)
    assert not any(f.kind == "MISSING_ORGAN" for f in report.findings)


def test_file_outside_registered_package_is_an_organ_candidate(tmp_path: Path):
    package = tmp_path / "sage" / "c2"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "helper.py").write_text("VALUE = 2\n", encoding="utf-8")
    (tmp_path / "sage" / "orphan.py").write_text("VALUE = 3\n", encoding="utf-8")
    catalog = _catalog(SubsystemRegistration(
        subsystem_id="c2",
        module_path="sage/c2/",
        relationship=JigsawRelationship.CORE,
        description="C2 package boundary",
    ))
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert any(f.kind == "UNDECLARED_ORGAN" and f.subject == "sage/orphan.py" for f in report.findings)
    assert not any(f.kind == "UNDECLARED_ORGAN" and f.subject == "sage/c2/helper.py" for f in report.findings)


def test_missing_organ_is_detected(tmp_path: Path):
    (tmp_path / "sage").mkdir()
    catalog = _catalog(SubsystemRegistration(
        subsystem_id="missing",
        module_path="sage/missing.py",
        relationship=JigsawRelationship.CORE,
        description="missing organ",
    ))
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert any(f.kind == "MISSING_ORGAN" and f.subject == "sage/missing.py" for f in report.findings)


def test_projection_filesystem_mutation_is_detected(tmp_path: Path):
    organ = tmp_path / "sage" / "projection.py"
    organ.parent.mkdir(parents=True)
    organ.write_text(
        "from pathlib import Path\n"
        "def render():\n"
        "    Path('state.txt').write_text('bad')\n", encoding="utf-8",
    )
    catalog = _catalog(SubsystemRegistration(
        subsystem_id="projection",
        module_path="sage/projection.py",
        relationship=JigsawRelationship.PROJECTION,
        description="projection",
    ))
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert any(f.kind == "PROJECTION_MUTATION_SURFACE" for f in report.findings)


def test_duplicate_authority_is_detected(tmp_path: Path):
    organ = tmp_path / "sage" / "authority.py"
    organ.parent.mkdir(parents=True)
    organ.write_text("VALUE = 1\n", encoding="utf-8")
    catalog = _catalog(
        SubsystemRegistration(
            subsystem_id="a",
            module_path="sage/authority.py",
            relationship=JigsawRelationship.CORE,
            description="a",
            authoritative_domain="state",
        ),
        SubsystemRegistration(
            subsystem_id="b",
            module_path="sage/authority.py",
            relationship=JigsawRelationship.CORE,
            description="b",
            authoritative_domain="state",
        ),
    )
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert any(f.kind == "DUPLICATE_AUTHORITY" and f.subject == "state" for f in report.findings)


def test_invalid_dependency_edge_is_detected(tmp_path: Path):
    organ = tmp_path / "sage" / "consumer.py"
    organ.parent.mkdir(parents=True)
    organ.write_text("from sage.missing import value\n", encoding="utf-8")
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=[])
    assert any(f.kind == "INVALID_DEPENDENCY_EDGE" for f in report.findings)


def test_dependency_cycle_is_detected(tmp_path: Path):
    root = tmp_path / "sage"
    root.mkdir(parents=True)
    (root / "a.py").write_text("from sage.b import value\nvalue = 1\n", encoding="utf-8")
    (root / "b.py").write_text("from sage.a import value\nvalue = 2\n", encoding="utf-8")
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=[])
    assert any(f.kind == "DEPENDENCY_CYCLE" for f in report.findings)


def test_experimental_to_core_coupling_is_detected(tmp_path: Path):
    core = tmp_path / "sage" / "core.py"
    experimental = tmp_path / "sage" / "experimental" / "probe.py"
    core.parent.mkdir(parents=True)
    experimental.parent.mkdir(parents=True)
    core.write_text("VALUE = 1\n", encoding="utf-8")
    experimental.write_text("from sage.core import VALUE\n", encoding="utf-8")
    catalog = _catalog(
        SubsystemRegistration(
            subsystem_id="core",
            module_path="sage/core.py",
            relationship=JigsawRelationship.CORE,
            description="core",
        ),
        SubsystemRegistration(
            subsystem_id="probe",
            module_path="sage/experimental/probe.py",
            relationship=JigsawRelationship.SERVICE,
            description="probe",
        ),
    )
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert any(f.kind == "EXPERIMENTAL_TO_CORE_COUPLING" for f in report.findings)


def test_experimental_to_core_package_coupling_is_detected(tmp_path: Path):
    core = tmp_path / "sage" / "core"
    experimental = tmp_path / "sage" / "experimental" / "probe.py"
    core.mkdir(parents=True)
    experimental.parent.mkdir(parents=True)
    (core / "__init__.py").write_text("VALUE = 1\n", encoding="utf-8")
    (core / "helper.py").write_text("VALUE = 2\n", encoding="utf-8")
    experimental.write_text("from sage.core.helper import VALUE\n", encoding="utf-8")
    catalog = _catalog(
        SubsystemRegistration(
            subsystem_id="core",
            module_path="sage/core/",
            relationship=JigsawRelationship.CORE,
            description="core package",
        ),
        SubsystemRegistration(
            subsystem_id="probe",
            module_path="sage/experimental/probe.py",
            relationship=JigsawRelationship.SERVICE,
            description="probe",
        ),
    )
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=catalog)
    assert any(f.kind == "EXPERIMENTAL_TO_CORE_COUPLING" for f in report.findings)


def test_cognition_canonical_mutation_is_detected(tmp_path: Path):
    organ = tmp_path / "sage" / "experimental" / "cognitive" / "memory.py"
    organ.parent.mkdir(parents=True)
    organ.write_text(
        "from pathlib import Path\n"
        "def mutate():\n"
        "    Path('state.json').write_text('{}')\n", encoding="utf-8",
    )
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=[])
    assert any(f.kind == "COGNITION_CANONICAL_MUTATION" for f in report.findings)


def test_git_head_mismatch_fails_closed(tmp_path: Path):
    (tmp_path / "sage").mkdir()
    (tmp_path / "sage" / "organ.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "fixture"], check=True)
    report = evaluate_organism_integrity(HEAD, root_dir=str(tmp_path), catalog=[])
    assert any(f.kind == "HEAD_MISMATCH" for f in report.findings)


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
