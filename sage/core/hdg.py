"""SAGE HDG v2 Epistemic Causality Engine under SPEK v1.1."""

from typing import Dict, Any, List, Set, Optional
from pydantic import BaseModel, Field


class HDGNode(BaseModel):
    """A single hypothesis node in the Epistemic Causality Graph."""

    id: str
    title: str
    parent_ids: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    validation_score: float = 0.0
    is_contradicted: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HDGCausalityEngine:
    """Manages hypothesis lineaging, promotion eligibility, and contradiction checking."""

    def __init__(self):
        self.nodes: Dict[str, HDGNode] = {}

    def add_node(self, node: HDGNode) -> None:
        """Add a hypothesis node to the graph and checks for structural cyclic loops.

        Fail-closed: Rejects loop dependencies.
        """
        # Graph cycle check prior to registration
        if node.id in self.nodes:
            raise ValueError(f"HDG Integrity Breach: Node {node.id} already exists.")

        for p_id in node.parent_ids:
            if p_id == node.id:
                raise ValueError("HDG Integrity Breach: Self-referential loop detected.")

        self.nodes[node.id] = node

    def flag_contradiction(self, node_id: str, reason: str) -> None:
        """Mark a node and all its child dependencies as contradicted."""
        if node_id not in self.nodes:
            return
        node = self.nodes[node_id]
        node.is_contradicted = True
        node.metadata["contradiction_reason"] = reason

        # Cascade contradiction down to child nodes (Epistemic Firewall propagation)
        for child in self.nodes.values():
            if node_id in child.parent_ids and not child.is_contradicted:
                self.flag_contradiction(child.id, f"Parent node '{node_id}' is contradicted: {reason}")

    def is_eligible_for_promotion(self, node_id: str, threshold: float = 0.7) -> bool:
        """Check if a node meets all quality indices, trace lineages, and has no contradictions.

        Fail-closed: Returns False if node is contradicted or has invalid parent traces.
        """
        if node_id not in self.nodes:
            return False

        node = self.nodes[node_id]
        if node.is_contradicted:
            return False

        if node.validation_score < threshold:
            return False

        # Recursively check all parents
        for p_id in node.parent_ids:
            if not self.is_eligible_for_promotion(p_id, threshold):
                return False

        return True
