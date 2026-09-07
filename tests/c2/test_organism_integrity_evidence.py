"""Adversarial tests for Organism Integrity evidence binding."""

from pathlib import Path
import subprocess

import pytest

from sage.c2.organism_integrity import evaluate_organism_integrity
from sage.c2.organism_integrity_evidence import (
    bind_integrity_evidence,
    verify_integrity_evidence_binding,
)


def _git_fixture(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    (root / "sage").mkdir(parents=True)
    (root / "sage" / "organ.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    head = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    return root, head


def test_binding_is_reproducible(tmp_path: Path):
    root, head = _git_fixture(tmp_path)
    report = evaluate_organism_integrity(head, root_dir=str(root), catalog=[])
    first = bind_integrity_evidence(report, root_dir=str(root))
    second = bind_integrity_evidence(report, root_dir=str(root))
    assert first == second
    assert len(first.repository_state_digest) == 64
    assert len(first.findings_digest) == 64
    assert len(first.bound_digest) == 64


def test_binding_changes_when_observed_file_bytes_change(tmp_path: Path):
    root, head = _git_fixture(tmp_path)
    report = evaluate_organism_integrity(head, root_dir=str(root), catalog=[])
    original = bind_integrity_evidence(report, root_dir=str(root))

    (root / "sage" / "organ.py").write_text("VALUE = 2\n", encoding="utf-8")
    changed = bind_integrity_evidence(report, root_dir=str(root))

    assert changed.repository_state_digest != original.repository_state_digest
    assert changed.bound_digest != original.bound_digest


def test_binding_verification_fails_on_file_drift(tmp_path: Path):
    root, head = _git_fixture(tmp_path)
    report = evaluate_organism_integrity(head, root_dir=str(root), catalog=[])
    binding = bind_integrity_evidence(report, root_dir=str(root))

    (root / "sage" / "organ.py").write_text("VALUE = 99\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="binding mismatch|repository_state_digest|bound_digest"):
        verify_integrity_evidence_binding(report, binding, root_dir=str(root))


def test_binding_fails_closed_on_head_drift(tmp_path: Path):
    root, head = _git_fixture(tmp_path)
    report = evaluate_organism_integrity(head, root_dir=str(root), catalog=[])
    binding = bind_integrity_evidence(report, root_dir=str(root))

    (root / "sage" / "organ.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "drift"], check=True)

    with pytest.raises(AssertionError, match="HEAD mismatch"):
        verify_integrity_evidence_binding(report, binding, root_dir=str(root))


def test_binding_rejects_path_escape(tmp_path: Path):
    root, head = _git_fixture(tmp_path)
    report = evaluate_organism_integrity(head, root_dir=str(root), catalog=[])
    escaped = report.__class__(
        exact_git_head=report.exact_git_head,
        discovered_modules=("../outside.py",),
        declared_modules=report.declared_modules,
        findings=report.findings,
        digest=report.digest,
    )
    with pytest.raises(AssertionError, match="escapes repository root"):
        bind_integrity_evidence(escaped, root_dir=str(root))
