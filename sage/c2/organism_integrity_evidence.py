"""Cryptographic evidence binding for the SAGE Organism Integrity report.

The structural integrity evaluator describes repository reality. This module adds a
separate evidence layer that binds that report to the exact Git HEAD and the bytes
of every implementation file the evaluator observed. It does not become C2
authority and does not promote evidence into runtime state.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

from sage.c2.organism_integrity import OrganismIntegrityReport


@dataclass(frozen=True)
class OrganismEvidenceBinding:
    """Reproducible cryptographic binding for one integrity report."""

    exact_git_head: str
    repository_state_digest: str
    findings_digest: str
    bound_digest: str


def _repository_head(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _findings_digest(report: OrganismIntegrityReport) -> str:
    material = "|".join(
        f"{finding.kind}:{finding.subject}:{finding.detail}"
        for finding in report.findings
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _repository_state_digest(root: Path, paths: tuple[str, ...]) -> str:
    """Hash the exact bytes and repository-relative paths observed by the report."""
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise AssertionError(f"Evidence path escapes repository root: {relative}") from exc
        if not path.is_file():
            raise AssertionError(f"Evidence path is missing or not a file: {relative}")
        data = path.read_bytes()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(data)).encode("ascii"))
        digest.update(b"\0")
        digest.update(data)
        digest.update(b"\0")
    return digest.hexdigest()


def _bound_digest(
    exact_git_head: str,
    repository_state_digest: str,
    findings_digest: str,
    discovered_modules: tuple[str, ...],
    declared_modules: tuple[str, ...],
) -> str:
    material = "\n".join(
        (
            exact_git_head,
            repository_state_digest,
            findings_digest,
            "\n".join(sorted(discovered_modules)),
            "\n".join(sorted(declared_modules)),
        )
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def bind_integrity_evidence(
    report: OrganismIntegrityReport,
    root_dir: str = ".",
) -> OrganismEvidenceBinding:
    """Bind an integrity report to the exact repository state it observed.

    The operation fails closed if the supplied Git HEAD no longer matches or if
    any implementation file recorded by the report has changed or disappeared.
    """
    root = Path(root_dir).resolve()
    observed_head = _repository_head(root)
    if observed_head != report.exact_git_head:
        raise AssertionError(
            "Evidence binding HEAD mismatch: "
            f"expected {report.exact_git_head}, observed {observed_head}."
        )

    repository_state_digest = _repository_state_digest(root, report.discovered_modules)
    findings_digest = _findings_digest(report)
    bound_digest = _bound_digest(
        report.exact_git_head,
        repository_state_digest,
        findings_digest,
        report.discovered_modules,
        report.declared_modules,
    )
    return OrganismEvidenceBinding(
        exact_git_head=report.exact_git_head,
        repository_state_digest=repository_state_digest,
        findings_digest=findings_digest,
        bound_digest=bound_digest,
    )


def verify_integrity_evidence_binding(
    report: OrganismIntegrityReport,
    binding: OrganismEvidenceBinding,
    root_dir: str = ".",
) -> None:
    """Recompute and verify a previously issued evidence binding."""
    if binding.exact_git_head != report.exact_git_head:
        raise AssertionError("Evidence binding report HEAD does not match.")

    expected = bind_integrity_evidence(report, root_dir=root_dir)
    if expected != binding:
        raise AssertionError("Organism integrity evidence binding mismatch.")
