"""Capability Graph Engine for SAGE C2.

Discovers, inventories, and maps repository capability nodes across core, experimental,
and C2 surfaces into an interconnected dependency graph. Classifies capability status
(IMPLEMENTED, TESTED, INTEGRATED, REUSABLE, DORMANT) and ranks candidate mission vectors
based on capability delta and surface depth.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from sage.c2.build_jump_wave import FlightMissionSpec


class CapabilityExecutionStatus(str, Enum):
    DORMANT = "DORMANT"
    IMPLEMENTED = "IMPLEMENTED"
    TESTED = "TESTED"
    INTEGRATED = "INTEGRATED"
    REUSABLE = "REUSABLE"


@dataclass(frozen=True)
class CapabilityNode:
    capability_id: str
    name: str
    source_path: str
    status: CapabilityExecutionStatus
    test_paths: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    classes: tuple[str, ...] = ()
    functions: tuple[str, ...] = ()
    description: str = ""

    def compute_digest(self) -> str:
        payload = {
            "capability_id": self.capability_id,
            "name": self.name,
            "source_path": self.source_path,
            "status": self.status.value,
            "test_paths": sorted(self.test_paths),
            "dependencies": sorted(self.dependencies),
            "classes": sorted(self.classes),
            "functions": sorted(self.functions),
        }
        raw = json.dumps(payload, sort_keys=True, separators=",:")
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CapabilityCandidateMission:
    mission_id: str
    frontier_name: str
    target_capability_id: str
    capability_delta: float
    flight_spec: FlightMissionSpec
    rationale: str


@dataclass(frozen=True)
class CapabilityGraphDigest:
    total_nodes: int
    status_counts: Mapping[str, int]
    edges_count: int
    graph_sha256: str
    candidate_missions_count: int


class CapabilityGraphEngine:
    """Discovers repository capability surface and builds a dynamic dependency graph."""

    def __init__(self, repo_root: Path | str | None = None):
        self.repo_root = Path(repo_root) if repo_root else Path(".")
        self.nodes: dict[str, CapabilityNode] = {}
        self.edges: list[tuple[str, str]] = []  # (source_id, target_id)

    def discover_repository_capabilities(self) -> dict[str, CapabilityNode]:
        """Scans sage/ and sage/experimental/ to build the full capability node graph."""
        self.nodes.clear()
        self.edges.clear()

        sage_dir = self.repo_root / "sage"
        if not sage_dir.exists():
            return {}

        all_py = sorted(sage_dir.glob("**/*.py"))
        for py_path in all_py:
            if py_path.name.startswith("__"):
                continue

            rel_path = str(py_path.relative_to(self.repo_root))
            cap_id = rel_path.replace("/", ".").replace(".py", "")

            try:
                content = py_path.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(py_path))
            except Exception:
                continue

            classes = tuple(sorted(n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)))
            functions = tuple(
                sorted(
                    n.name
                    for n in ast.walk(tree)
                    if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")
                )
            )

            # Discover dependencies via import analysis
            deps = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("sage."):
                            deps.add(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("sage."):
                        deps.add(node.module)

            # Locate associated test files
            test_paths = self._find_associated_tests(py_path.stem)

            # Determine execution status
            status = self._classify_status(rel_path, classes, functions, test_paths, deps)

            node = CapabilityNode(
                capability_id=cap_id,
                name=py_path.stem.replace("_", " ").title(),
                source_path=rel_path,
                status=status,
                test_paths=tuple(sorted(test_paths)),
                dependencies=tuple(sorted(deps)),
                classes=classes,
                functions=functions,
                description=ast.get_docstring(tree) or "",
            )
            self.nodes[cap_id] = node

            for dep_id in deps:
                self.edges.append((cap_id, dep_id))

        return self.nodes

    def _find_associated_tests(self, stem: str) -> list[str]:
        tests_dir = self.repo_root / "tests"
        if not tests_dir.exists():
            return []

        matched = []
        possible_names = [f"test_{stem}.py", f"test_{stem}_wave.py", f"test_{stem}_contract.py"]

        for test_file in tests_dir.glob("**/*.py"):
            if test_file.name in possible_names or stem in test_file.name:
                matched.append(str(test_file.relative_to(self.repo_root)))

        return sorted(list(set(matched)))

    def _classify_status(
        self,
        rel_path: str,
        classes: tuple[str, ...],
        functions: tuple[str, ...],
        test_paths: list[str],
        deps: set[str],
    ) -> CapabilityExecutionStatus:
        if not classes and not functions:
            return CapabilityExecutionStatus.DORMANT

        has_tests = len(test_paths) > 0

        if "sage/experimental/" in rel_path:
            if not has_tests:
                return CapabilityExecutionStatus.IMPLEMENTED
            if len(deps) > 2:
                return CapabilityExecutionStatus.INTEGRATED
            return CapabilityExecutionStatus.TESTED

        if "sage/c2/" in rel_path or "sage/runtime/" in rel_path:
            if has_tests and len(deps) > 1:
                return CapabilityExecutionStatus.REUSABLE
            if has_tests:
                return CapabilityExecutionStatus.TESTED
            return CapabilityExecutionStatus.INTEGRATED

        if has_tests:
            return CapabilityExecutionStatus.TESTED
        return CapabilityExecutionStatus.IMPLEMENTED

    def rank_candidate_missions(self, limit: int = 5) -> list[CapabilityCandidateMission]:
        """Ranks capability nodes by capability delta (gap between status & potential) into dynamic candidate missions."""
        if not self.nodes:
            self.discover_repository_capabilities()

        candidates: list[CapabilityCandidateMission] = []

        # Target nodes that are in experimental/
        for cap_id, node in self.nodes.items():
            if "sage/experimental/" not in node.source_path:
                continue

            # Capability delta score: lower status -> higher potential delta
            status_weights = {
                CapabilityExecutionStatus.DORMANT: 1.0,
                CapabilityExecutionStatus.IMPLEMENTED: 0.8,
                CapabilityExecutionStatus.TESTED: 0.6,
                CapabilityExecutionStatus.INTEGRATED: 0.3,
                CapabilityExecutionStatus.REUSABLE: 0.1,
            }
            weight = status_weights.get(node.status, 0.5)
            dep_factor = min(1.0, len(node.dependencies) * 0.15)
            class_factor = min(1.0, (len(node.classes) + len(node.functions)) * 0.1)

            delta = round(weight * 0.5 + dep_factor * 0.3 + class_factor * 0.2, 4)

            stem = Path(node.source_path).stem
            test_refs = list(node.test_paths) if node.test_paths else [f"tests/c2/test_{stem}.py"]

            flight_spec = FlightMissionSpec(
                flight_id="F1",  # Anonymous temporary slot placeholder
                frontier_name=f"CAP-GRAPH-{stem.upper()}",
                target_path=node.source_path,
                collision_zone=cap_id,
                evidence_ref=f"evidence_capture/waves/cap_graph/{stem}_receipt.json",
                pr_or_change=f"Capability Graph Expansion mission for {node.name}",
                test_references=test_refs,
            )

            candidate = CapabilityCandidateMission(
                mission_id=f"mission-{stem}",
                frontier_name=f"FRONTIER-{stem.upper()}",
                target_capability_id=cap_id,
                capability_delta=delta,
                flight_spec=flight_spec,
                rationale=f"Promote experimental node {cap_id} ({node.status.value}) to C2 dynamic execution vector.",
            )
            candidates.append(candidate)

        # Sort descending by capability delta
        candidates.sort(key=lambda c: c.capability_delta, reverse=True)
        return candidates[:limit]

    def get_digest(self) -> CapabilityGraphDigest:
        """Computes cryptographic digest of the current capability graph state."""
        if not self.nodes:
            self.discover_repository_capabilities()

        counts = {status.value: 0 for status in CapabilityExecutionStatus}
        for node in self.nodes.values():
            counts[node.status.value] += 1

        node_digests = [node.compute_digest() for node in sorted(self.nodes.values(), key=lambda n: n.capability_id)]
        raw_graph = json.dumps({"nodes": node_digests, "edges": sorted(self.edges)}, sort_keys=True)
        graph_sha = hashlib.sha256(raw_graph.encode("utf-8")).hexdigest()

        return CapabilityGraphDigest(
            total_nodes=len(self.nodes),
            status_counts=counts,
            edges_count=len(self.edges),
            graph_sha256=graph_sha,
            candidate_missions_count=len(self.nodes),
        )
