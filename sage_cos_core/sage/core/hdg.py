"""SAGE HDG v2 Epistemic Causality Engine."""

import json
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from sage_cos_core.sage.core.models import HypothesisNode


class HDGEngine:
    """HDG v2 Epistemic Causality Engine.

    Tracks hypotheses, parents, evidence ancestry, validation scores, and contradiction markers.
    Fails closed if the storage is corrupted.
    """

    def __init__(self, storage_path: str | Path | None = None):
        """Initialize HDG Engine."""
        self.storage_path = Path(
            storage_path or ".sage/validation/audit/hdg_causality.json"
        )
        self._lock = threading.Lock()
        self.nodes: Dict[str, HypothesisNode] = {}
        self.load_graph()

    def load_graph(self) -> None:
        """Load HDG from disk. Fails closed with an exception if data is corrupted."""
        with self._lock:
            if not self.storage_path.exists():
                self.nodes = {}
                return

        try:
            with open(self.storage_path, "r") as f:
                content = f.read().strip()
                if not content:
                    self.nodes = {}
                    return
                data = json.loads(content)
        except Exception as e:
            # Corrupted HDG state must fail closed
            raise RuntimeError(f"CRITICAL INTEGRITY FAILURE: HDG state is corrupted: {e!s}")

        if not isinstance(data, dict):
            raise RuntimeError("CRITICAL INTEGRITY FAILURE: HDG format is invalid")

        self.nodes = {}
        for node_id, fields in data.items():
            try:
                self.nodes[node_id] = HypothesisNode(
                    node_id=node_id,
                    parent_ids=fields.get("parent_ids", []),
                    evidence_references=fields.get("evidence_references", []),
                    validation_score=fields.get("validation_score", 0.0),
                    contradiction_markers=fields.get("contradiction_markers", []),
                    promotion_eligible=fields.get("promotion_eligible", False),
                    metadata=fields.get("metadata", {}),
                )
            except Exception as e:
                raise RuntimeError(f"CRITICAL INTEGRITY FAILURE: Failed to load node {node_id}: {e!s}")

    def save_graph(self) -> None:
        """Atomically persist the HDG to disk."""
        with self._lock:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)

            # Build serializable dictionary
            data = {
                node_id: {
                    "node_id": node.node_id,
                    "parent_ids": node.parent_ids,
                    "evidence_references": node.evidence_references,
                    "validation_score": node.validation_score,
                    "contradiction_markers": node.contradiction_markers,
                    "promotion_eligible": node.promotion_eligible,
                    "metadata": node.metadata,
                }
                for node_id, node in self.nodes.items()
            }

            # Atomic write
            temp_path = self.storage_path.with_suffix(".tmp")
            try:
                with open(temp_path, "w") as f:
                    json.dump(data, f, indent=2)
                temp_path.replace(self.storage_path)
            except OSError as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise RuntimeError(f"Failed to persist HDG causality graph: {e!s}")

    def add_node(self, node: HypothesisNode) -> None:
        """Add a hypothesis node and check its ancestry and contradiction markers."""
        # Check parent node references
        for parent_id in node.parent_ids:
            if parent_id not in self.nodes:
                raise ValueError(
                    f"Ancestry Broken: Parent hypothesis node '{parent_id}' does not exist in graph."
                )

        # Detect contradictions automatically
        contradiction_markers = self.detect_contradictions(node)
        node.contradiction_markers = contradiction_markers

        # Store in-memory
        self.nodes[node.node_id] = node
        self.save_graph()

    def get_node(self, node_id: str) -> Optional[HypothesisNode]:
        """Retrieve a node from the HDG."""
        return self.nodes.get(node_id)

    def detect_contradictions(self, node: HypothesisNode) -> List[str]:
        """Check for contradictions against existing nodes in the graph."""
        markers = []
        claim = node.metadata.get("claim")
        if not claim:
            return markers

        for existing in self.nodes.values():
            existing_claim = existing.metadata.get("claim")
            if not existing_claim:
                continue

            # Case 1: Opposite claims detected in claim strings
            if claim.lower().startswith("not ") and claim[4:].lower() == existing_claim.lower():
                markers.append(f"Contradiction: opposite of node {existing.node_id}")
            elif existing_claim.lower().startswith("not ") and existing_claim[4:].lower() == claim.lower():
                markers.append(f"Contradiction: opposite of node {existing.node_id}")

            # Case 2: Direct metadata tag contradicts existing tag
            if "contradicts" in node.metadata and node.metadata["contradicts"] == existing.node_id:
                markers.append(f"Contradiction declared: conflicts with node {existing.node_id}")
            if "contradicts" in existing.metadata and existing.metadata["contradicts"] == node.node_id:
                markers.append(f"Contradiction declared by existing node {existing.node_id}")

        return markers

    def get_ancestry(self, node_id: str) -> List[str]:
        """Traverse up the graph and return the complete ancestral lineage list of node IDs."""
        ancestry = []
        node = self.get_node(node_id)
        if not node:
            return ancestry

        queue = list(node.parent_ids)
        visited = set()
        while queue:
            curr_id = queue.pop(0)
            if curr_id not in visited:
                visited.add(curr_id)
                ancestry.append(curr_id)
                curr_node = self.get_node(curr_id)
                if curr_node:
                    queue.extend(curr_node.parent_ids)

        return ancestry
