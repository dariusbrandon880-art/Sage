"""Whole-organism structural integrity checks for the SAGE Jigsaw model.

Jigsaw is the structural self-model; it is not C2 authority.  This module compares
repository reality with the canonical Jigsaw catalog and reports structural gaps
without promoting the report into runtime state.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from pathlib import Path

from sage.c2.capability_graph import CapabilityGraphEngine
from sage.c2.organism_jigsaw import SubsystemRegistration, get_canonical_subsystem_catalog


@dataclass(frozen=True)
class OrganismIntegrityFinding:
    kind: str
    subject: str
    detail: str


@dataclass(frozen=True)
class OrganismIntegrityReport:
    exact_git_head: str
    discovered_modules: tuple[str, ...]
    declared_modules: tuple[str, ...]
    findings: tuple[OrganismIntegrityFinding, ...]
    digest: str

    @property
    def passed(self) -> bool:
        return not self.findings


@dataclass(frozen=True)
class _DiscoveredModule:
    path: str
    imports: tuple[str, ...]
    writes: tuple[str, ...]


def _python_modules(root: Path) -> tuple[_DiscoveredModule, ...]:
    """Discover executable Python organs from the repository, excluding caches."""
    modules: list[_DiscoveredModule] = []
    sage_root = root / "sage"
    if not sage_root.exists():
        return ()
    for path in sorted(sage_root.rglob("*.py")):
        if any(part in {"__pycache__", ".git"} for part in path.parts):
            continue
        relative = path.relative_to(root).as_posix()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        imports: set[str] = set()
        writes: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name for a in node.names if a.name.startswith("sage."))
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("sage."):
                imports.add(node.module)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"write_text", "write_bytes", "unlink", "replace", "rename"}:
                    writes.add(node.func.attr)
        modules.append(_DiscoveredModule(relative, tuple(sorted(imports)), tuple(sorted(writes))))
    return tuple(modules)


def _normalize_declared_path(module_path: str, root: Path) -> str:
    path = root / module_path
    if path.is_dir():
        init = path / "__init__.py"
        if init.exists():
            return init.relative_to(root).as_posix()
        return path.relative_to(root).as_posix().rstrip("/")
    return path.relative_to(root).as_posix()


def _finding_digest(findings: tuple[OrganismIntegrityFinding, ...]) -> str:
    material = "|".join(f"{f.kind}:{f.subject}:{f.detail}" for f in findings)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def discover_repository_organs(root_dir: str = ".") -> tuple[str, ...]:
    """Return deterministic repository Python-organ paths.

    The existing capability graph remains the discovery intelligence for its
    supported surfaces; this integrity layer additionally inventories the full
    executable ``sage`` tree because Jigsaw completeness cannot be inferred from
    a partial capability surface.
    """
    root = Path(root_dir).resolve()
    # Instantiate the existing graph engine so discovery remains connected to the
    # repository-native capability inventory rather than creating another graph.
    CapabilityGraphEngine(root).discover(exact_git_head="0" * 40)
    return tuple(module.path for module in _python_modules(root))


def evaluate_organism_integrity(
    exact_git_head: str,
    root_dir: str = ".",
    catalog: list[SubsystemRegistration] | None = None,
) -> OrganismIntegrityReport:
    """Compare actual repository Python organs with the canonical Jigsaw map."""
    root = Path(root_dir).resolve()
    discovered = _python_modules(root)
    actual = {m.path for m in discovered}
    catalog = catalog if catalog is not None else get_canonical_subsystem_catalog()
    declared = {
        _normalize_declared_path(sub.module_path, root)
        for sub in catalog
    }

    findings: list[OrganismIntegrityFinding] = []
    for path in sorted(actual - declared):
        findings.append(OrganismIntegrityFinding(
            kind="UNDECLARED_ORGAN",
            subject=path,
            detail="Executable Python organ exists on disk but is absent from the canonical Jigsaw catalog.",
        ))
    for path in sorted(declared - actual):
        findings.append(OrganismIntegrityFinding(
            kind="MISSING_ORGAN",
            subject=path,
            detail="Canonical Jigsaw registration has no matching executable Python organ on disk.",
        ))

    declared_by_path = {
        _normalize_declared_path(sub.module_path, root): sub for sub in catalog
    }
    for module in discovered:
        if module.path not in declared_by_path:
            continue
        # Projection organs must not directly encode filesystem mutation. This is
        # a structural signal only; canonical state ownership remains elsewhere.
        registration = declared_by_path[module.path]
        if registration.relationship.value == "PROJECTION" and module.writes:
            findings.append(OrganismIntegrityFinding(
                kind="PROJECTION_MUTATION_SURFACE",
                subject=module.path,
                detail=f"Projection contains filesystem mutation calls: {module.writes}",
            ))

    finding_tuple = tuple(findings)
    return OrganismIntegrityReport(
        exact_git_head=exact_git_head,
        discovered_modules=tuple(sorted(actual)),
        declared_modules=tuple(sorted(declared)),
        findings=finding_tuple,
        digest=_finding_digest(finding_tuple),
    )


def assert_organism_integrity(exact_git_head: str, root_dir: str = ".") -> OrganismIntegrityReport:
    """Fail closed when repository structure diverges from the canonical Jigsaw map."""
    report = evaluate_organism_integrity(exact_git_head=exact_git_head, root_dir=root_dir)
    if not report.passed:
        summary = "; ".join(f"{f.kind}:{f.subject}" for f in report.findings)
        raise AssertionError(f"Organism integrity failure: {summary}")
    return report
