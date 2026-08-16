"""Adversarial & Governed Brain Unit Tests for SAGE/SAGI Cognitive Kernel Integration.

Tests SAGI Research Graph knowledge integration into Cognitive State, Prefrontal Cortex
executive decision gating under bridged knowledge/regressions, persistence, and fresh-process rehydration.
"""

import json
import pytest
from pathlib import Path

from sage.experimental.cognitive import (
    CognitiveState,
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveOperatorConstraints,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveCompletedMilestone,
    PrefrontalCortexSimulator,
    DecisionGateOutcome,
    SAGIResearchKnowledgeBridge,
    CognitivePersistenceManager,
)
from sage.experimental.sagi.research_graph import (
    SAGIResearchNode,
    SAGIResearchGraph,
)


@pytest.fixture
def base_cognitive_state() -> CognitiveState:
    """Fixture producing a clean, valid CognitiveState."""
    return CognitiveState(
        agent_identity=CognitiveAgentIdentity(
            agent_id="agent_jules_001",
            name="Jules Cognitive Operator",
            role="COGNITIVE_OPERATOR",
            authority_level="TIER_2_EXECUTION",
            governance_tier="GOVERNED_TIER_2",
        ),
        active_mission=CognitiveActiveMission(
            mission_id="msn_brain_001",
            objective="Execute governed cognitive research and decision integration",
        ),
        operator_constraints=CognitiveOperatorConstraints(
            authorized_agents=["agent_jules_001"],
            permitted_paths=["sage/experimental/cognitive/"],
        ),
        confidence_state=CognitiveConfidenceState(
            overall_confidence=0.95,
            last_updated=1000.0,
        ),
        next_action=CognitiveNextAction(
            action_id="act_brain_001",
            description="Execute governed cognitive research step",
            assigned_agent="agent_jules_001",
        ),
    )


def test_valid_cognitive_transition(base_cognitive_state: CognitiveState):
    """TEST 1: Valid cognitive transition proceeds when state aligns with active mission."""
    pfc = PrefrontalCortexSimulator()
    report = pfc.evaluate_decision(base_cognitive_state)
    assert report.outcome == DecisionGateOutcome.PROCEED
    assert report.checks_performed["mission_alignment"] is True


def test_invalid_cognitive_transition_completed_milestone(base_cognitive_state: CognitiveState):
    """TEST 2: Invalid transition proposing a completed milestone action is BLOCKED."""
    base_cognitive_state.completed_milestones.append(
        CognitiveCompletedMilestone(
            milestone_id="act_brain_001",
            completed_at=900.0,
            evidence_hash="sha256_milestone_evidence_hash",
        )
    )
    pfc = PrefrontalCortexSimulator()
    report = pfc.evaluate_decision(base_cognitive_state)
    assert report.outcome == DecisionGateOutcome.BLOCK
    assert "Completed milestone reopening/modification blocked" in report.reason


def test_missing_context_requests_clarification(base_cognitive_state: CognitiveState):
    """TEST 3: Missing proposed next action causes PFC to REQUEST_CLARIFICATION."""
    base_cognitive_state.next_action = None
    pfc = PrefrontalCortexSimulator()
    report = pfc.evaluate_decision(base_cognitive_state)
    assert report.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "No next action proposed" in report.reason


def test_conflicting_state_low_confidence(base_cognitive_state: CognitiveState):
    """TEST 4: Conflicting/uncertain cognitive state with low overall confidence requests clarification."""
    base_cognitive_state.confidence_state.overall_confidence = 0.35
    pfc = PrefrontalCortexSimulator()
    report = pfc.evaluate_decision(base_cognitive_state)
    assert report.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "Confidence level is too low" in report.reason


def test_missing_provenance_evidence_blocks(base_cognitive_state: CognitiveState):
    """TEST 5: Action requiring specific evidence references fails when missing from validated facts."""
    base_cognitive_state.next_action.required_evidence = ["sagi_research_node:sha256_missing_node"]
    pfc = PrefrontalCortexSimulator()
    report = pfc.evaluate_decision(base_cognitive_state)
    assert report.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "requires evidence references" in report.reason


def test_corrupted_persisted_state_rejection(tmp_path: Path):
    """TEST 6: Corrupted or invalid persisted cognitive state file raises validation error on rehydration."""
    corrupted_file = tmp_path / "corrupted_state.json"
    corrupted_file.write_text('{"agent_identity": "NOT_A_DICT"}', encoding="utf-8")

    pm = CognitivePersistenceManager(ledger_path=corrupted_file)
    with pytest.raises(Exception):
        pm.load_state()


def test_unauthorized_action_request_blocked(base_cognitive_state: CognitiveState):
    """TEST 7: Action proposed by an unauthorized agent ID is BLOCKED."""
    base_cognitive_state.agent_identity.agent_id = "agent_unauthorized_999"
    pfc = PrefrontalCortexSimulator()
    report = pfc.evaluate_decision(base_cognitive_state)
    assert report.outcome == DecisionGateOutcome.BLOCK
    assert "not in the operator's authorized agents list" in report.reason


def test_uncertainty_insufficient_evidence_bridging(base_cognitive_state: CognitiveState):
    """TEST 8: Ingesting research failure nodes produces CognitiveForbiddenRegression and tracks reasoning."""
    graph = SAGIResearchGraph(expected_identity_anchor="identity_anchor_001")
    node_failed = SAGIResearchNode(
        node_id="node_failed_01",
        cycle_id="cycle_01",
        identity_anchor="identity_anchor_001",
        candidate_signature="sig_fail_12345",
        guardian_result="REJECTED",
        failure_state={"reason": "CRPL-F1 Metadata non-influence violation"},
    )
    graph.add_node(node_failed)

    bridge = SAGIResearchKnowledgeBridge(expected_identity_anchor="identity_anchor_001")
    receipt = bridge.integrate_research_graph(base_cognitive_state, graph)

    assert receipt.forbidden_regressions_added == 1
    assert len(base_cognitive_state.forbidden_regressions) == 1
    regr = base_cognitive_state.forbidden_regressions[0]
    assert "CRPL-F1 Metadata non-influence violation" in regr.description


def test_deterministic_reconstruction_cross_process(base_cognitive_state: CognitiveState, tmp_path: Path):
    """TEST 9: Fresh-process rehydration restores exact CognitiveState, identity, facts, and regressions."""
    graph = SAGIResearchGraph(expected_identity_anchor="identity_anchor_001")
    node_ok = SAGIResearchNode(
        node_id="node_ok_01",
        cycle_id="cycle_01",
        identity_anchor="identity_anchor_001",
        candidate_signature="sig_ok_12345",
        guardian_result="APPROVED",
    )
    graph.add_node(node_ok)

    bridge = SAGIResearchKnowledgeBridge(expected_identity_anchor="identity_anchor_001")
    bridge.integrate_research_graph(base_cognitive_state, graph)

    ledger_file = tmp_path / "cognitive_ledger.json"
    pm1 = CognitivePersistenceManager(ledger_path=ledger_file)
    pm1.save_state(base_cognitive_state)

    # Instantiate fresh persistence manager representing new session / process
    pm2 = CognitivePersistenceManager(ledger_path=ledger_file)
    rehydrated = pm2.load_state()

    assert rehydrated.agent_identity.agent_id == base_cognitive_state.agent_identity.agent_id
    assert len(rehydrated.validated_facts) == 1
    assert rehydrated.validated_facts[0].fact_id == "fact_sagi_node_ok_01"


def test_governance_fail_closed_identity_mismatch(base_cognitive_state: CognitiveState):
    """TEST 10: Ingesting research graph with mismatched identity anchor fails closed with ValueError."""
    graph = SAGIResearchGraph(expected_identity_anchor="identity_anchor_FOREIGN")
    bridge = SAGIResearchKnowledgeBridge(expected_identity_anchor="identity_anchor_EXPECTED")

    with pytest.raises(ValueError, match="Cognitive Governance Identity Boundary Violation"):
        bridge.integrate_research_graph(base_cognitive_state, graph)


def test_true_independent_process_boundary_reconstruction(tmp_path: Path):
    """TEST 11: True independent process boundary verification using a spawned Python subprocess."""
    import subprocess
    import sys

    ledger_file = tmp_path / "subprocess_cognitive_ledger.json"

    # Process A: Python subprocess creates, bridges, and persists CognitiveState to disk
    script_process_a = f"""
import sys
from pathlib import Path
from sage.experimental.cognitive import (
    CognitiveState,
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveOperatorConstraints,
    CognitiveConfidenceState,
    CognitiveNextAction,
    SAGIResearchKnowledgeBridge,
    CognitivePersistenceManager,
)
from sage.experimental.sagi.research_graph import SAGIResearchNode, SAGIResearchGraph

graph = SAGIResearchGraph(expected_identity_anchor="identity_process_001")
node_ok = SAGIResearchNode(
    node_id="node_proc_01",
    cycle_id="cycle_proc_01",
    identity_anchor="identity_process_001",
    candidate_signature="sig_process_A_12345",
    guardian_result="APPROVED",
)
graph.add_node(node_ok)

state = CognitiveState(
    agent_identity=CognitiveAgentIdentity(
        agent_id="agent_subprocess_A",
        name="Process A Agent",
        role="WRITER",
        authority_level="TIER_2_EXECUTION",
        governance_tier="GOVERNED_TIER_2",
    ),
    active_mission=CognitiveActiveMission(
        mission_id="msn_proc_01",
        objective="Execute process separation persistence test",
    ),
    operator_constraints=CognitiveOperatorConstraints(
        authorized_agents=["agent_subprocess_A"],
    ),
    confidence_state=CognitiveConfidenceState(
        overall_confidence=0.92,
        last_updated=2000.0,
    ),
    next_action=CognitiveNextAction(
        action_id="act_proc_01",
        description="Execute process separation action",
        assigned_agent="agent_subprocess_A",
    ),
)

bridge = SAGIResearchKnowledgeBridge(expected_identity_anchor="identity_process_001")
bridge.integrate_research_graph(state, graph)

pm = CognitivePersistenceManager(ledger_path=r"{ledger_file}")
pm.save_state(state)
sys.exit(0)
"""

    res_a = subprocess.run([sys.executable, "-c", script_process_a], capture_output=True, text=True)
    assert res_a.returncode == 0, f"Process A failed: {res_a.stderr}"
    assert ledger_file.exists(), "Process A failed to create persisted state ledger file."

    # Process B: Completely separate Python subprocess loads state from disk and executes PFC evaluation
    script_process_b = f"""
import sys
from pathlib import Path
from sage.experimental.cognitive import (
    CognitivePersistenceManager,
    PrefrontalCortexSimulator,
    DecisionGateOutcome,
)

pm = CognitivePersistenceManager(ledger_path=r"{ledger_file}")
rehydrated_state = pm.load_state()

assert rehydrated_state.agent_identity.agent_id == "agent_subprocess_A"
assert len(rehydrated_state.validated_facts) == 1
assert rehydrated_state.validated_facts[0].fact_id == "fact_sagi_node_proc_01"

pfc = PrefrontalCortexSimulator()
report = pfc.evaluate_decision(rehydrated_state)
assert report.outcome == DecisionGateOutcome.PROCEED

print("PROCESS_B_SUCCESS")
sys.exit(0)
"""

    res_b = subprocess.run([sys.executable, "-c", script_process_b], capture_output=True, text=True)
    assert res_b.returncode == 0, f"Process B failed: {res_b.stderr}"
    assert "PROCESS_B_SUCCESS" in res_b.stdout
