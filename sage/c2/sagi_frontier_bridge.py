"""Bounded SAGI ResearchGraph -> C2 frontier candidate bridge.

SAGI remains proposal/research authority. This module only translates a verified
research node into the existing canonical C2 FrontierCandidate shape; C2's
FrontierAdmissionEngine remains the admission authority.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from sage.c2.frontier_admission import FrontierCandidate, FrontierState
from sage.experimental.sagi.research_graph import SAGIResearchNode


class SAGIFrontierCandidate(BaseModel):
    """Evidence-bound proposal envelope produced from one SAGI research node."""

    candidate: FrontierCandidate
    research_node_id: str
    research_node_sha256: str
    identity_anchor: str
    research_only: bool = True


class SAGIFrontierBridge:
    """Translate verified SAGI research output into a bounded C2 proposal."""

    def __init__(self, identity_anchor: str):
        if not identity_anchor:
            raise ValueError("C2 bridge requires a non-empty identity anchor")
        self.identity_anchor = identity_anchor

    def to_frontier_candidate(
        self,
        node: SAGIResearchNode,
        *,
        target: str,
        base_sha: str,
        collision_zone: str,
        evidence_required: Optional[List[str]] = None,
        stop_condition: str,
        dependencies: Optional[List[str]] = None,
    ) -> SAGIFrontierCandidate:
        """Fail closed unless the research node is verified, approved, and anchored."""
        if node.guardian_result.upper() != "APPROVED":
            raise ValueError("ResearchGraph node was not approved by the SAGI guardian")
        if node.identity_anchor != self.identity_anchor:
            raise ValueError("ResearchGraph identity anchor does not match C2 bridge anchor")
        if len(node.node_sha256) != 64 or node.node_sha256 != node.compute_sha256():
            raise ValueError("ResearchGraph node integrity verification failed")
        if not target or not base_sha or not collision_zone or not stop_condition:
            raise ValueError("C2 frontier proposal requires target, base_sha, collision_zone, and stop_condition")

        frontier_id = f"sagi-{node.node_id}"
        source = (
            f"SAGI ResearchGraph node={node.node_id};"
            f"node_sha256={node.node_sha256};"
            f"identity_anchor={node.identity_anchor}"
        )
        candidate = FrontierCandidate(
            frontier_id=frontier_id,
            target=target,
            source=source,
            state=FrontierState.UNSTARTED,
            base_sha=base_sha,
            dependencies=dependencies or [],
            collision_zone=collision_zone,
            evidence_required=evidence_required or [f"sagi://research-graph/{node.node_id}"],
            stop_condition=stop_condition,
        )
        return SAGIFrontierCandidate(
            candidate=candidate,
            research_node_id=node.node_id,
            research_node_sha256=node.node_sha256,
            identity_anchor=node.identity_anchor,
        )
