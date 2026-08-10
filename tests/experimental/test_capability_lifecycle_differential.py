"""Focused differential test proving that validated capability experience dynamically alters preflight decisions."""

import json
from pathlib import Path
from sage.capability_registry import SAGEOperationalCapabilityRegistry
from sage.experimental.cognitive.state_schema import (
    CognitiveState,
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveOperatorConstraints,
    CognitiveValidatedFact
)
from sage.experimental.cognitive.prefrontal_cortex import PrefrontalCortexSimulator, DecisionGateOutcome


def test_capability_lifecycle_differential():
    """Verify that validated experience dynamically changes preflight decision outcomes.

    Differential Test:
    - Case A (No Validated Capability): Preflight returns REQUEST_CLARIFICATION.
    - Case B (Validated Capability Available): Preflight returns PROCEED.
    """
    pfc = PrefrontalCortexSimulator()

    # 1. Setup default state
    agent = CognitiveAgentIdentity(
        agent_id="agent_jules_sage",
        name="Jules",
        role="Senior Software Engineer",
        authority_level="TIER_1_COORDINATOR",
        governance_tier="TIER_1_COORDINATOR",
    )
    mission = CognitiveActiveMission(
        mission_id="msn_differential_test",
        objective="Verify differential preflight capabilities",
        status="RUNNING"
    )
    constraints = CognitiveOperatorConstraints(authorized_agents=["agent_jules_sage"])
    confidence = CognitiveConfidenceState(overall_confidence=1.0, last_updated=0.0)

    # Propose action that requires validated capability evidence
    next_action = CognitiveNextAction(
        action_id="task_differential_execution",
        description="Verify differential preflight capabilities",
        assigned_agent="agent_jules_sage",
        required_evidence=["evidence_capture/ccl_orchestrator_evidence.json"]
    )

    state_a = CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action,
        validated_facts=[]  # Empty facts
    )

    # --- Case A: No Validated Capability ---
    report_a = pfc.evaluate_decision(state_a)
    assert report_a.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "missing from validated facts" in report_a.reason

    # --- Case B: Validated Capability Available ---
    # Query the SAGE Operational Capability Registry on disk (existing primitive)
    registry = SAGEOperationalCapabilityRegistry()
    cap = registry.get_capability("CAP-PML-RELIABILITY")
    assert cap is not None
    assert "evidence_capture/ccl_orchestrator_evidence.json" in cap.evidence_references

    # Inject the validated capability evidence as a cognitive fact (the connection)
    fact = CognitiveValidatedFact(
        fact_id="fact_validated_pml",
        statement="SML capability is validated",
        confidence_score=1.0,
        evidence_references=cap.evidence_references
    )

    state_b = CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action,
        validated_facts=[fact]  # Injected validated capability fact
    )

    report_b = pfc.evaluate_decision(state_b)
    # The decision changes from REQUEST_CLARIFICATION to PROCEED!
    assert report_b.outcome == DecisionGateOutcome.PROCEED
    assert "possesses required evidence" in report_b.reason
