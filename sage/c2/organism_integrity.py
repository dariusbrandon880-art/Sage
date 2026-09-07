"""Whole-organism structural integrity checks for the SAGE Jigsaw model.

Jigsaw is the structural self-model; it is not C2 authority. This module compares
repository reality with the canonical Jigsaw catalog and reports structural gaps
without promoting the report into runtime state.
"""

from __future__ import annotations

import ast
import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path

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


def _declares_path(module_path: str, actual_path: str, root: Path) -> bool:
    """Return whether a registration covers a file or a registered package tree."""
    path = root / module_path
    if path.is_dir():
        return actual_path == module_path.rstrip("/") or actual_path.startswith(module_path.rstrip("/") + "/")
    return _normalize_declared_path(module_path, root) == actual_path


def _module_name(path: str) -> str:
    return path.removesuffix(".py").replace("/", ".")


def _resolve_import(import_name: str, actual: set[str]) -> str | None:
    candidates = [import_name, f"{import_name}.__init__"]
    for candidate in candidates:
        if f"{candidate}.py" in {_module_name(p) + ".py" for p in actual}:
            return candidate
    # Normalise a package import to its package __init__.py representation.
    package = import_name.replace(".", "/")
    if f"{package}/__init__.py" in actual:
        return f"{package}/__init__.py"
    if f"{package}.py" in actual:
        return f"{package}.py"
    return None


def _finding_digest(findings: tuple[OrganismIntegrityFinding, ...]) -> str:
    material = "|".join(f"{f.kind}:{f.subject}:{f.detail}" for f in findings)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _repository_head(root: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def evaluate_organism_integrity(
    exact_git_head: str,
    root_dir: str = ".",
    catalog: list[SubsystemRegistration] | None = None,
) -> OrganismIntegrityReport:
    """Compare repository organs, dependency structure, and authority boundaries."""
    root = Path(root_dir).resolve()
    discovered = _python_modules(root)
    actual = {m.path for m in discovered}
    catalog = catalog if catalog is not None else get_canonical_subsystem_catalog()

    findings: list[OrganismIntegrityFinding] = []
    observed_head = _repository_head(root)
    if observed_head is not None and observed_head != exact_git_head:
        findings.append(OrganismIntegrityFinding(
            kind="HEAD_MISMATCH",
            subject=exact_git_head,
            detail=f"Evaluated repository HEAD is {observed_head}, not the supplied exact Git HEAD.",
        ))

    declared = {
        _normalize_declared_path(sub.module_path, root)
        for sub in catalog
    }
    for path in sorted(actual):
        if not any(_declares_path(sub.module_path, path, root) for sub in catalog):
            findings.append(OrganismIntegrityFinding(
                kind="UNDECLARED_ORGAN",
                subject=path,
                detail="Executable Python organ exists on disk but is absent from the canonical Jigsaw catalog.",
            ))
    for sub in catalog:
        if not any(_declares_path(sub.module_path, path, root) for path in actual):
            findings.append(OrganismIntegrityFinding(
                kind="MISSING_ORGAN",
                subject=_normalize_declared_path(sub.module_path, root),
                detail="Canonical Jigsaw registration has no matching executable Python organ on disk.",
            ))

    domain_map: dict[str, list[str]] = {}
    for sub in catalog:
        if sub.authoritative_domain:
            domain_map.setdefault(sub.authoritative_domain, []).append(sub.subsystem_id)
    for domain, subsystem_ids in sorted(domain_map.items()):
        if len(subsystem_ids) > 1:
            findings.append(OrganismIntegrityFinding(
                kind="DUPLICATE_AUTHORITY",
                subject=domain,
                detail=f"Multiple canonical subsystems claim the same authoritative domain: {subsystem_ids}.",
            ))

    registration_by_path = {
        sub.module_path: sub for sub in catalog
        if not (root / sub.module_path).is_dir()
    }
    core_paths = {
        _normalize_declared_path(sub.module_path, root)
        for sub in catalog if sub.relationship.value == "CORE"
    }

    adjacency: dict[str, set[str]] = {module.path: set() for module in discovered}
    module_by_name = {_module_name(module.path): module.path for module in discovered}
    for module in discovered:
        for imported in module.imports:
            target = _resolve_import(imported, actual)
            if target is None:
                findings.append(OrganismIntegrityFinding(
                    kind="INVALID_DEPENDENCY_EDGE",
                    subject=module.path,
                    detail=f"Repository-local import does not resolve to an executable organ: {imported}.",
                ))
                continue
            target_path = target if target in actual else module_by_name.get(target)
            if target_path:
                adjacency[module.path].add(target_path)

        registration = next(
            (sub for sub in catalog if _declares_path(sub.module_path, module.path, root)),
            None,
        )
        if registration and registration.relationship.value == "PROJECTION" and module.writes:
            findings.append(OrganismIntegrityFinding(
                kind="PROJECTION_MUTATION_SURFACE",
                subject=module.path,
                detail=f"Projection contains filesystem mutation calls: {module.writes}",
            ))
        if module.path.startswith("sage/experimental/"):
            for target in adjacency[module.path]:
                if target in core_paths:
                    findings.append(OrganismIntegrityFinding(
                        kind="EXPERIMENTAL_TO_CORE_COUPLING",
                        subject=module.path,
                        detail=f"Experimental organ imports canonical CORE organ {target}.",
                    ))
            if any(write in module.writes for write in ("write_text", "write_bytes", "unlink", "replace", "rename")) and (
                "/cognitive/" in module.path or "/sagi/" in module.path
            ):
                findings.append(OrganismIntegrityFinding(
                    kind="COGNITION_CANONICAL_MUTATION",
                    subject=module.path,
                    detail="Experimental cognition surface contains direct filesystem mutation calls.",
                ))

    # Tarjan-style SCC detection identifies actual import cycles while keeping the
    # evaluator deterministic and independent of import-time side effects.
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in sorted(adjacency[node]):
            if target not in indices:
                strongconnect(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while True:
                target = stack.pop()
                on_stack.remove(target)
                component.append(target)
                if target == node:
                    break
            if len(component) > 1 or node in adjacency[node]:
                cycle = ",".join(sorted(component))
                findings.append(OrganismIntegrityFinding(
                    kind="DEPENDENCY_CYCLE",
                    subject=cycle,
                    detail="Repository-local import graph contains a cycle.",
                ))

    for node in sorted(adjacency):
        if node not in indices:
            strongconnect(node)

    finding_tuple = tuple(sorted(findings, key=lambda f: (f.kind, f.subject, f.detail)))
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
