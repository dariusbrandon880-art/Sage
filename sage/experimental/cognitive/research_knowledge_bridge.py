"""SAGI Research Knowledge Bridge & Cognitive Integration Module.

Bridges SAGI Research Graph knowledge nodes and cryptographic receipts directly
into SAGE Cognitive State (CognitiveValidatedFact and CognitiveForbiddenRegression)
and Prefrontal Cortex executive control.
"""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.cognitive.state_schema import (
    CognitiveState,
    CognitiveValidatedFact,
    CognitiveForbiddenRegression,
)
from sage.experimental.sagi.research_graph import (
    SAGIResearchNode,
    SAGIResearchGraph,
    SAGIResearchGraphReceipt,
)


class ResearchKnowledgeIntegrationReceipt(BaseModel):
    """Execution receipt emitted upon bridging SAGI Research Graph into Cognitive State."""

    receipt_id: str
    state_agent_id: str
    identity_anchor: str
    nodes_ingested: int
    facts_added: int
    forbidden_regressions_added: int
    cognitive_state_sha256: str
    timestamp: float = Field(default_factory=time.time)
    receipt_sha256: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.receipt_sha256:
            self.receipt_sha256 = self.compute_sha256()

    def compute_sha256(self) -> str:
        """Compute deterministic SHA-256 hash over integration receipt."""
        payload = {
            "receipt_id": self.receipt_id,
            "state_agent_id": self.state_agent_id,
            "identity_anchor": self.identity_anchor,
            "nodes_ingested": self.nodes_ingested,
            "facts_added": self.facts_added,
            "forbidden_regressions_added": self.forbidden_regressions_added,
            "cognitive_state_sha256": self.cognitive_state_sha256,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class SAGIResearchKnowledgeBridge:
    """Bridge for integrating SAGI Research Graph nodes into SAGE Executive Cognitive State."""

    def __init__(self, expected_identity_anchor: Optional[str] = None):
        self.expected_identity_anchor = expected_identity_anchor

    def integrate_research_graph(
        self,
        cognitive_state: CognitiveState,
        research_graph: SAGIResearchGraph
    ) -> ResearchKnowledgeIntegrationReceipt:
        """Ingest all research nodes from a SAGIResearchGraph into CognitiveState.

        Approved research nodes -> CognitiveValidatedFact
        Rejected/failed research nodes -> CognitiveForbiddenRegression
        Enforces strict fail-closed identity anchor verification between research graph and cognitive state.
        """
        # Identity boundary verification (fail closed if bridge expects an identity anchor)
        if self.expected_identity_anchor is not None:
            if research_graph.expected_identity_anchor != self.expected_identity_anchor:
                graph_anchor_str = research_graph.expected_identity_anchor[:12] if research_graph.expected_identity_anchor else "None"
                expected_anchor_str = self.expected_identity_anchor[:12]
                raise ValueError(
                    f"Cognitive Governance Identity Boundary Violation: Research graph identity anchor "
                    f"'{graph_anchor_str}' does not match expected identity anchor '{expected_anchor_str}'."
                )

        facts_before = len(cognitive_state.validated_facts)
        regressions_before = len(cognitive_state.forbidden_regressions)

        existing_fact_ids = {f.fact_id for f in cognitive_state.validated_facts}
        existing_regression_ids = {r.regression_id for r in cognitive_state.forbidden_regressions}

        nodes_ingested = 0

        for nid in sorted(research_graph.nodes.keys()):
            node = research_graph.nodes[nid]
            nodes_ingested += 1

            if node.guardian_result == "APPROVED":
                fact_id = f"fact_sagi_{node.node_id}"
                if fact_id not in existing_fact_ids:
                    fact = CognitiveValidatedFact(
                        fact_id=fact_id,
                        statement=(
                            f"SAGI Research Candidate {node.candidate_signature[:12]} approved in cycle "
                            f"{node.cycle_id} under identity {node.identity_anchor[:12]}."
                        ),
                        evidence_references=[
                            f"sagi_research_node:{node.node_sha256}",
                            f"sagi_cycle:{node.cycle_id}",
                        ],
                        confidence_score=1.0,
                    )
                    cognitive_state.validated_facts.append(fact)
                    existing_fact_ids.add(fact_id)
            else:
                regression_id = f"regr_sagi_{node.node_id}"
                if regression_id not in existing_regression_ids:
                    reason_desc = "Unknown research failure"
                    if node.failure_state and isinstance(node.failure_state, dict):
                        reason_desc = str(node.failure_state.get("reason", "Research guardian rejection"))

                    restricted = [
                        node.candidate_signature,
                        node.node_id,
                        f"rejected_candidate_{node.candidate_signature[:12]}",
                    ]

                    regression = CognitiveForbiddenRegression(
                        regression_id=regression_id,
                        description=(
                            f"SAGI Research Failure in node {node.node_id} (cycle {node.cycle_id}): "
                            f"{reason_desc}"
                        ),
                        restricted_actions=restricted,
                        blocked_states=[node.cycle_id],
                    )
                    cognitive_state.forbidden_regressions.append(regression)
                    existing_regression_ids.add(regression_id)

        facts_added = len(cognitive_state.validated_facts) - facts_before
        regressions_added = len(cognitive_state.forbidden_regressions) - regressions_before

        # Compute deterministic state SHA256
        state_serialized = cognitive_state.model_dump_json()
        state_sha256 = hashlib.sha256(state_serialized.encode("utf-8")).hexdigest()

        receipt_id = f"rcpt_knowledge_bridge_{int(time.time()*1000)}"
        receipt = ResearchKnowledgeIntegrationReceipt(
            receipt_id=receipt_id,
            state_agent_id=cognitive_state.agent_identity.agent_id,
            identity_anchor=research_graph.expected_identity_anchor or "unanchored",
            nodes_ingested=nodes_ingested,
            facts_added=facts_added,
            forbidden_regressions_added=regressions_added,
            cognitive_state_sha256=state_sha256,
        )

        return receipt
