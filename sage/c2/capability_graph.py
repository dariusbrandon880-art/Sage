"""Repository-native capability graph discovery for C2 mission selection.

The graph is discovery intelligence, not authority. It inventories executable
surfaces, links implementation/test references, classifies lifecycle state, and
ranks distinct capability-gap candidates. Flight slots remain anonymous; the
mission candidate owns semantic identity.
"""
from __future__ import annotations

import ast
import hashlib
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CapabilityNode:
    node_id: str
    path: str
    surface: str
    entry_points: tuple[str, ...] = ()
    test_references: tuple[str, ...] = ()
    implementation_status: str = "IMPLEMENTED"
    integration_status: str = "DORMANT"
    reusable: bool = False
    dependency_paths: tuple[str, ...] = ()


@dataclass(frozen=True)
class CapabilityMissionCandidate:
    mission_id: str
    target_path: str
    surface: str
    before: str
    after: str
    leverage: float
    depth_gap: float
    verification_burden: float
    rationale: str


@dataclass(frozen=True)
class CapabilityGraph:
    exact_git_head: str
    nodes: tuple[CapabilityNode, ...]
    digest: str


class CapabilityGraphEngine:
    """Discover the repository's real capability surface without slot semantics."""

    SURFACES = (
        ("sagi", "SAGI"),
        ("airspace", "Airspace"),
        ("cognitive", "Cognitive"),
        ("sports_quant", "Sports"),
        ("sports_longitudinal", "Sports"),
        ("c2", "C2"),
        ("observatory", "Observatory"),
        ("media_perception", "Continuity/Perception"),
        ("continuity", "Continuity/Perception"),
        ("act", "ACT"),
    )

    def __init__(self, root_dir: str = ".") -> None:
        self.root = Path(root_dir).resolve()

    def _surface_for(self, relative_path: str) -> str:
        lowered = relative_path.lower()
        for token, surface in self.SURFACES:
            if token in lowered:
                return surface
        return "Core"

    def _entry_points(self, source: str) -> tuple[str, ...]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ()
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not node.name.startswith("_"):
                    names.append(node.name)
        return tuple(sorted(set(names)))

    def _imports(self, source: str) -> tuple[str, ...]:
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ()
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names if alias.name.startswith("sage."))
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("sage."):
                imports.add(node.module)
        return tuple(sorted(imports))

    def _tests_for(self, relative_path: str) -> tuple[str, ...]:
        stem = Path(relative_path).stem
        refs: list[str] = []
        tests_root = self.root / "tests"
        if not tests_root.exists():
            return ()
        for path in tests_root.rglob("test_*.py"):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if stem in text or stem in path.stem:
                refs.append(path.relative_to(self.root).as_posix())
        return tuple(sorted(set(refs)))

    def discover(self, exact_git_head: str) -> CapabilityGraph:
        roots = [self.root / "sage" / "experimental", self.root / "sage" / "c2"]
        nodes: list[CapabilityNode] = []
        for root in roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.py")):
                if path.name.startswith("__"):
                    continue
                relative = path.relative_to(self.root).as_posix()
                try:
                    source = path.read_text(encoding="utf-8")
                except OSError:
                    continue
                tests = self._tests_for(relative)
                entry_points = self._entry_points(source)
                deps = self._imports(source)
                integration = "TESTED" if tests else "DORMANT"
                reusable = bool(entry_points and tests)
                node_id = "CAPNODE-" + hashlib.sha256(relative.encode()).hexdigest()[:16]
                nodes.append(CapabilityNode(
                    node_id=node_id,
                    path=relative,
                    surface=self._surface_for(relative),
                    entry_points=entry_points,
                    test_references=tests,
                    implementation_status="IMPLEMENTED",
                    integration_status=integration,
                    reusable=reusable,
                    dependency_paths=deps,
                ))
        material = "|".join(
            f"{n.node_id}:{n.path}:{n.surface}:{','.join(n.entry_points)}:{','.join(n.test_references)}:{n.integration_status}:{n.reusable}:{','.join(n.dependency_paths)}"
            for n in nodes
        )
        digest = hashlib.sha256(f"{exact_git_head}|{material}".encode()).hexdigest()
        return CapabilityGraph(exact_git_head=exact_git_head, nodes=tuple(nodes), digest=digest)

    def rank_missions(self, graph: CapabilityGraph, limit: int = 8) -> tuple[CapabilityMissionCandidate, ...]:
        if limit < 1:
            raise ValueError("mission limit must be positive")
        candidates: list[CapabilityMissionCandidate] = []
        for node in graph.nodes:
            # Prioritize under-integrated but testable surfaces: these are real
            # capabilities that can become operationally useful without inventing
            # a feature from nothing.
            depth_gap = 1.0 if node.integration_status == "DORMANT" else 0.45
            leverage = min(1.0, 0.45 + 0.08 * len(node.entry_points) + (0.20 if node.reusable else 0.0))
            verification_burden = 0.25 if node.test_references else 0.75
            if not node.entry_points:
                continue
            candidates.append(CapabilityMissionCandidate(
                mission_id=f"MISSION-{node.node_id}",
                target_path=node.path,
                surface=node.surface,
                before=f"SAGE has {node.path} implemented but not yet exposed as a governed reusable capability.",
                after=f"SAGE exposes {node.path} as a discoverable governed capability with explicit verification lineage.",
                leverage=leverage,
                depth_gap=depth_gap,
                verification_burden=verification_burden,
                rationale=f"Surface={node.surface}; entry_points={len(node.entry_points)}; tests={len(node.test_references)}; reusable={node.reusable}.",
            ))
        ranked = sorted(candidates, key=lambda c: (0.45*c.leverage + 0.40*c.depth_gap - 0.15*c.verification_burden, c.surface, c.target_path), reverse=True)
        selected: list[CapabilityMissionCandidate] = []
        surfaces: set[str] = set()
        for candidate in ranked:
            if candidate.surface in surfaces:
                continue
            selected.append(candidate)
            surfaces.add(candidate.surface)
            if len(selected) == limit:
                break
        if len(selected) < limit:
            selected.extend(c for c in ranked if c not in selected) 
            selected = selected[:limit]
        return tuple(selected)
