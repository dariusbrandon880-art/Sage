"""SAGI Phase 3 Research Graph & Knowledge Integration.

Implements SAGIResearchNode, SAGIResearchGraph, and SAGIResearchGraphReceipt
converting search loop receipts and candidate observations into a structured,
identity-anchored, deterministic research knowledge graph.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.sagi.search_loop import SAGISearchLoopReceipt
from sage.experimental.sagi.controller import SAGIEvolutionReceipt


class SAGIResearchNode(BaseModel):
    """Research node representing an observed research candidate or search cycle."""
    node_id: str
    cycle_id: str
    identity_anchor: str
    candidate_signature: str
    guardian_result: str
    measurement_summary: Dict[str, Any] = Field(default_factory=dict)
    failure_state: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=time.time)
    node_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.node_sha256:
            self.node_sha256 = self.compute_sha256()

    def compute_sha256(self) -> str:
        """Compute deterministic SHA-256 hash over research node fields."""
        payload = {
            "node_id": self.node_id,
            "cycle_id": self.cycle_id,
            "identity_anchor": self.identity_anchor,
            "candidate_signature": self.candidate_signature,
            "guardian_result": self.guardian_result,
            "measurement_summary": self.measurement_summary,
            "has_failure_state": self.failure_state is not None
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SAGIResearchGraphReceipt(BaseModel):
    """Deterministic research graph receipt emitted by SAGIResearchGraph."""
    graph_id: str
    nodes_added: int
    cycles_indexed: int
    failure_patterns_tracked: int
    identity_anchor: str
    research_only: bool = True
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    receipt_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.receipt_sha256:
            self.receipt_sha256 = self.compute_sha256()

    def compute_sha256(self) -> str:
        """Compute deterministic SHA-256 hash over graph receipt contents."""
        payload = {
            "graph_id": self.graph_id,
            "nodes_added": self.nodes_added,
            "cycles_indexed": self.cycles_indexed,
            "failure_patterns_tracked": self.failure_patterns_tracked,
            "identity_anchor": self.identity_anchor,
            "research_only": self.research_only
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SAGIResearchGraph:
    """Isolated, read-only Research Knowledge Graph for SAGI Digital Twin Brain."""

    def __init__(
        self,
        graph_id: str = "sagi_research_graph_omega",
        expected_identity_anchor: Optional[str] = None
    ):
        self.graph_id = graph_id
        self.expected_identity_anchor = expected_identity_anchor
        self.nodes: Dict[str, SAGIResearchNode] = {}
        self.cycles_indexed: set[str] = set()

    def add_node(self, node: SAGIResearchNode) -> None:
        """Add a research node to the graph, enforcing identity anchor verification."""
        if self.expected_identity_anchor is None:
            self.expected_identity_anchor = node.identity_anchor

        # Identity Boundary Protection: Reject nodes with mismatched identity anchors
        if node.identity_anchor != self.expected_identity_anchor:
            raise ValueError(
                f"SAGI Identity Boundary Violation: Node identity anchor '{node.identity_anchor[:12]}' "
                f"does not match expected graph identity anchor '{self.expected_identity_anchor[:12]}'."
            )

        self.nodes[node.node_id] = node
        self.cycles_indexed.add(node.cycle_id)

    def ingest_search_receipt(self, search_receipt: SAGISearchLoopReceipt) -> SAGIResearchNode:
        """Ingest a SAGISearchLoopReceipt and convert it into a SAGIResearchNode in the graph."""
        node_id = f"node_{search_receipt.cycle_id}_{len(self.nodes)+1}"
        guardian_res = "APPROVED" if search_receipt.guardian_checks_passed else "REJECTED"

        failure_state = None
        if search_receipt.candidates_rejected > 0 or not search_receipt.guardian_checks_passed:
            failure_state = {
                "rejected_count": search_receipt.candidates_rejected,
                "failure_memory_size": search_receipt.failure_memory_size,
                "guardian_passed": search_receipt.guardian_checks_passed
            }

        measurement_summary = {
            "tested": search_receipt.candidates_tested,
            "approved": search_receipt.candidates_approved,
            "rejected": search_receipt.candidates_rejected,
            "failure_memory_size": search_receipt.failure_memory_size
        }

        node = SAGIResearchNode(
            node_id=node_id,
            cycle_id=search_receipt.cycle_id,
            identity_anchor=search_receipt.identity_anchor,
            candidate_signature=search_receipt.receipt_sha256,
            guardian_result=guardian_res,
            measurement_summary=measurement_summary,
            failure_state=failure_state
        )

        self.add_node(node)
        return node

    def ingest_evolution_receipt(self, evolution_receipt: SAGIEvolutionReceipt, identity_anchor: str) -> SAGIResearchNode:
        """Ingest a single SAGIEvolutionReceipt into a SAGIResearchNode."""
        node_id = f"node_evo_{evolution_receipt.receipt_id}"

        failure_state = None
        if evolution_receipt.verification_status != "APPROVED":
            failure_state = {
                "reason": evolution_receipt.decision_reasoning,
                "failure_memory_count": evolution_receipt.failure_memory_count
            }

        node = SAGIResearchNode(
            node_id=node_id,
            cycle_id=f"cycle_{evolution_receipt.cycle_index}",
            identity_anchor=identity_anchor,
            candidate_signature=evolution_receipt.proposal_hash,
            guardian_result=evolution_receipt.verification_status,
            measurement_summary={
                "temperature": evolution_receipt.temperature_after,
                "mutation_radius": evolution_receipt.mutation_radius,
                "learning_metrics": evolution_receipt.learning_metrics
            },
            failure_state=failure_state
        )

        self.add_node(node)
        return node

    def query_nodes(self, guardian_result: Optional[str] = None, has_failures_only: bool = False) -> List[SAGIResearchNode]:
        """Query research nodes deterministically by guardian result or failure state."""
        results = []
        for nid in sorted(self.nodes.keys()):
            node = self.nodes[nid]
            if guardian_result and node.guardian_result != guardian_result:
                continue
            if has_failures_only and node.failure_state is None:
                continue
            results.append(node)
        return results

    def compute_graph_sha256(self) -> str:
        """Compute deterministic graph-wide SHA-256 hash across all ordered research nodes."""
        ordered_hashes = [self.nodes[k].node_sha256 for k in sorted(self.nodes.keys())]
        payload = {
            "graph_id": self.graph_id,
            "node_count": len(self.nodes),
            "expected_identity_anchor": self.expected_identity_anchor or "",
            "node_hashes": ordered_hashes
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def emit_graph_receipt(self) -> SAGIResearchGraphReceipt:
        """Emit a deterministic SAGIResearchGraphReceipt representing current graph state."""
        failure_nodes = [n for n in self.nodes.values() if n.failure_state is not None]
        receipt = SAGIResearchGraphReceipt(
            graph_id=self.graph_id,
            nodes_added=len(self.nodes),
            cycles_indexed=len(self.cycles_indexed),
            failure_patterns_tracked=len(failure_nodes),
            identity_anchor=self.expected_identity_anchor or "unanchored",
            research_only=True
        )
        return receipt
