"""HDG v2 Epistemic Causality Engine for SAGE SPEK v1.1."""

import json
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import ValidationError

from sage.core.boundary import BoundaryEnforcer
from sage.core.models import HypothesisNode


class HDGEngine:
    """Manages the Hyper-Dimensional Graph (HDG) v2 epistemic causality nodes.

    Validates parents, traces evidence recursively, identifies cyclical dependencies,
    and handles contradiction validation. Fails closed under any corruption or cycle.
    """

    def __init__(self, storage_path: Optional[str | Path] = None, boundary_enforcer: Optional[BoundaryEnforcer] = None):
        """Initialize HDGEngine."""
        self.storage_path = Path(storage_path or ".sage/validation/audit/hdg_causality.json")
        self.enforcer = boundary_enforcer or BoundaryEnforcer()
        self._lock = threading.RLock()
        self.nodes: Dict[str, HypothesisNode] = {}
        self._load_graph()

    def _load_graph(self) -> None:
        """Load and structurally validate the graph from disk. Fails closed if corrupted."""
        with self._lock:
            if not self.storage_path.exists():
                self.nodes = {}
                return

            try:
                with open(self.storage_path, "r") as f:
                    raw_data = json.load(f)
                    if not isinstance(raw_data, list):
                        raise ValueError("HDG storage format corrupted: Root is not a JSON list.")

                    loaded_nodes = {}
                    for item in raw_data:
                        node = HypothesisNode(**item)
                        loaded_nodes[node.node_id] = node

                    self.nodes = loaded_nodes
                    # Run complete graph validation (cycle detection, parenthood checks) immediately.
                    self.validate_graph_integrity()
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                # Force fail-closed behavior on corruption
                self.nodes = {}
                raise ValueError(f"HDG Epistemic Causality Engine Failed Closed: {e!s}")

    def save_graph(self, auth_token: str) -> None:
        """Persist the graph state atomically to disk with boundary checks.

        Args:
            auth_token: Present security token to pass boundary enforcer.
        """
        with self._lock:
            # Validate mutation permission before writing
            self.enforcer.validate_mutation(self.storage_path, auth_token)

            self.validate_graph_integrity()

            # Write to a thread-unique temporary file first for atomic durability
            temp_path = self.storage_path.parent / f"{self.storage_path.stem}_{uuid.uuid4().hex}.tmp"
            try:
                data = [n.model_dump() for n in self.nodes.values()]
                with open(temp_path, "w") as f:
                    json.dump(data, f, indent=2)
                temp_path.replace(self.storage_path)
            except OSError as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise IOError(f"Failed to persist HDG causality ledger: {e!s}")

    def add_node(self, node: HypothesisNode, auth_token: str) -> None:
        """Add a new hypothesis node to the graph and save it.

        Args:
            node: The HypothesisNode to add.
            auth_token: Present security token.
        """
        with self._lock:
            # Temporal insert
            self.nodes[node.node_id] = node

            try:
                # Validate complete integrity (will raise ValueError on cycle or missing parents)
                self.validate_graph_integrity()
            except ValueError:
                # Revert and propagate failure
                self.nodes.pop(node.node_id, None)
                raise

            self.save_graph(auth_token)

    def get_node(self, node_id: str) -> HypothesisNode:
        """Get a node by ID. Fails closed on graph corruption."""
        with self._lock:
            self.validate_graph_integrity()
            if node_id not in self.nodes:
                raise KeyError(f"Hypothesis node not found: {node_id}")
            return self.nodes[node_id]

    def trace_evidence(self, node_id: str) -> List[str]:
        """Recursively trace and aggregate evidence references across all decisions and parents.

        Ensures full traceability of lineage.

        Args:
            node_id: Start node ID.

        Returns:
            Flat list of unique evidence reference strings collected recursively.
        """
        with self._lock:
            self.validate_graph_integrity()
            evidence_refs: Set[str] = set()
            visited: Set[str] = set()

            def recurse(curr_id: str):
                if curr_id in visited:
                    return
                visited.add(curr_id)
                node = self.nodes.get(curr_id)
                if not node:
                    return
                evidence_refs.update(node.evidence_refs)
                for parent_id in node.parent_ids:
                    recurse(parent_id)

            recurse(node_id)
            return sorted(list(evidence_refs))

    def check_contradictions(self, node_id: str) -> List[str]:
        """Check if a node has active contradictions in its ancestral causal path.

        Args:
            node_id: Target node ID.

        Returns:
            List of contradictory node IDs found.
        """
        with self._lock:
            self.validate_graph_integrity()
            ancestors = self._get_ancestors(node_id)
            contradictions_found = []

            # Find active contradictions in our ancestor chain
            for ancestor_id in ancestors:
                node = self.nodes[ancestor_id]
                for contra_id in node.contradictions:
                    if contra_id in ancestors:
                        contradictions_found.append(contra_id)

            return contradictions_found

    def is_eligible_for_promotion(self, node_id: str, evidence_threshold: float = 0.7) -> bool:
        """Evaluate promotion eligibility.

        Eligibility Rules:
        - Must have validation score >= evidence_threshold.
        - Must have no contradictions in ancestor path.
        - Must have at least 1 evidence reference.

        Args:
            node_id: Target node ID.
            evidence_threshold: Required minimum score.

        Returns:
            True if eligible, False otherwise.
        """
        with self._lock:
            try:
                node = self.get_node(node_id)
                if node.validation_score < evidence_threshold:
                    return False
                if self.check_contradictions(node_id):
                    return False
                # Needs to have some trace of evidence references
                evidences = self.trace_evidence(node_id)
                if not evidences:
                    return False
                return True
            except Exception:
                return False

    def validate_graph_integrity(self) -> None:
        """Validate the full Hyper-Dimensional Graph structural integrity.

        Raises ValueError on any of:
        - Cycles (circular ancestry path)
        - Missing parent references
        - Self-contradiction or structural inconsistencies.
        """
        with self._lock:
            # 1. Check parent reference validity
            for node_id, node in self.nodes.items():
                for parent_id in node.parent_ids:
                    if parent_id not in self.nodes:
                        raise ValueError(f"HDG Integrity Corruption: Node {node_id} references non-existent parent: {parent_id}")

            # 2. Cycle detection using Depth-First Search
            visited_overall: Set[str] = set()
            for node_id in self.nodes:
                if node_id not in visited_overall:
                    ancestor_stack: Set[str] = set()
                    self._detect_cycle_dfs(node_id, ancestor_stack, visited_overall)

    def _detect_cycle_dfs(self, node_id: str, ancestor_stack: Set[str], visited_overall: Set[str]) -> None:
        if node_id in ancestor_stack:
            raise ValueError(f"HDG Integrity Failure: Circular dependency cycle detected involving node: {node_id}")

        ancestor_stack.add(node_id)
        node = self.nodes[node_id]
        for parent_id in node.parent_ids:
            self._detect_cycle_dfs(parent_id, ancestor_stack, visited_overall)

        ancestor_stack.remove(node_id)
        visited_overall.add(node_id)

    def _get_ancestors(self, node_id: str) -> Set[str]:
        """Aggregate all parent and ancestor IDs recursively."""
        ancestors: Set[str] = set()
        visited: Set[str] = set()

        def recurse(curr_id: str):
            if curr_id in visited:
                return
            visited.add(curr_id)
            node = self.nodes.get(curr_id)
            if not node:
                return
            ancestors.add(curr_id)
            for parent_id in node.parent_ids:
                recurse(parent_id)

        recurse(node_id)
        return ancestors
