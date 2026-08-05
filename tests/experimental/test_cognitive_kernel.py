"""Unit test suite for SAGE Cognitive Kernel and Prefrontal Cortex (PFC) Simulator."""

import time
import pytest
from sage.experimental.cognitive import (
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveValidatedFact,
    CognitiveCompletedMilestone,
    CognitiveForbiddenRegression,
    CognitiveOperatorConstraints,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveState,
    PrefrontalCortexSimulator,
    DecisionGateOutcome,
)


@pytest.fixture
def base_cognitive_state() -> CognitiveState:
    """Fixture to provide a standard approved base CognitiveState."""
    agent = CognitiveAgentIdentity(
        agent_id="agent_jules_sage",
        name="Jules",
        role="Senior Software Engineer",
        authority_level="TIER_1_COORDINATOR",
        governance_tier="TIER_1_COORDINATOR",
    )
    mission = CognitiveActiveMission(
        mission_id="mission_kernel_v1",
        objective="Develop the SAGE Cognitive Kernel foundation and prefrontal cortex simulator",
        milestones=["task_pfc_gate", "task_state_schema"],
        status="RUNNING",
    )
    fact = CognitiveValidatedFact(
        fact_id="fact_pfc_design",
        statement="Prefrontal Cortex architecture uses four safety gates",
        evidence_references=["doc_pfc_spec", "audit_pfc_gate_01"],
        confidence_score=1.0,
    )
    milestone = CognitiveCompletedMilestone(
        milestone_id="task_state_schema",
        completed_at=time.time() - 3600.0,
        evidence_hash="hash_state_schema_v1_validated",
        reopened_count=0,
    )
    forbidden = CognitiveForbiddenRegression(
        regression_id="regr_loop_prevention",
        description="Do not repeat the state planning loops indefinitely",
        restricted_actions=["unauthorized_replan"],
    )
    constraints = CognitiveOperatorConstraints(
        permitted_paths=["sage/experimental/cognitive/"],
        forbidden_paths=["sage/runtime/"],
        requires_approval=True,
        max_consecutive_failures=3,
        authorized_agents=["agent_jules_sage"],
    )
    confidence = CognitiveConfidenceState(
        overall_confidence=1.0,
        last_updated=time.time(),
        notes="Pruned baseline and validated schema",
    )
    next_action = CognitiveNextAction(
        action_id="task_pfc_gate",
        description="Develop and test the PFC simulator and gates",
        assigned_agent="agent_jules_sage",
        required_evidence=["audit_pfc_gate_01"],
    )

    return CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        validated_facts=[fact],
        completed_milestones=[milestone],
        forbidden_regressions=[forbidden],
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action,
    )


def test_valid_mission_proceeds(base_cognitive_state):
    """Verify that a standard, fully aligned, authorized, and evidenced mission is allowed to PROCEED."""
    simulator = PrefrontalCortexSimulator()
    report = simulator.evaluate_decision(base_cognitive_state)

    assert report.outcome == DecisionGateOutcome.PROCEED
    assert "aligns with active mission" in report.reason
    assert report.checks_performed["mission_alignment"] is True
    assert report.checks_performed["completed_work_protection"] is True
    assert report.checks_performed["constraint_validation"] is True
    assert report.checks_performed["evidence_requirement_detection"] is True


def test_completed_milestone_reopening_blocked(base_cognitive_state):
    """Verify that attempting to re-execute or reopening a completed milestone is BLOCKED."""
    simulator = PrefrontalCortexSimulator()

    # Propose next action that targets an already completed milestone
    base_cognitive_state.next_action = CognitiveNextAction(
        action_id="task_state_schema",  # Already in completed_milestones
        description="Re-execute task_state_schema schema creation",
        assigned_agent="agent_jules_sage",
    )

    report = simulator.evaluate_decision(base_cognitive_state)
    assert report.outcome == DecisionGateOutcome.BLOCK
    assert "Completed milestone reopening/modification blocked" in report.reason


def test_missing_context_requests_clarification(base_cognitive_state):
    """Verify that proposed actions with missing description or missing required evidence request clarification."""
    simulator = PrefrontalCortexSimulator()

    # 1. Test missing proposed action
    base_cognitive_state.next_action = None
    report_no_action = simulator.evaluate_decision(base_cognitive_state)
    assert report_no_action.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "No next action proposed" in report_no_action.reason

    # 2. Test blank description in proposed action (missing context)
    base_cognitive_state.next_action = CognitiveNextAction(
        action_id="task_pfc_gate",
        description="",
        assigned_agent="agent_jules_sage",
    )
    report_blank_desc = simulator.evaluate_decision(base_cognitive_state)
    assert report_blank_desc.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "missing crucial context" in report_blank_desc.reason

    # 3. Test missing required evidence
    base_cognitive_state.next_action = CognitiveNextAction(
        action_id="task_pfc_gate",
        description="Develop and test the PFC simulator and gates",
        assigned_agent="agent_jules_sage",
        required_evidence=["missing_evidence_audit_token"],
    )
    report_missing_evidence = simulator.evaluate_decision(base_cognitive_state)
    assert report_missing_evidence.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "requires evidence references" in report_missing_evidence.reason


def test_invalid_authority_blocked(base_cognitive_state):
    """Verify that actions proposed by an agent with invalid authority or unauthorized identifier are BLOCKED."""
    simulator = PrefrontalCortexSimulator()

    # 1. Agent not in authorized_agents list
    base_cognitive_state.operator_constraints.authorized_agents = ["authorized_supervisor_node"]
    report_unauthorized_id = simulator.evaluate_decision(base_cognitive_state)
    assert report_unauthorized_id.outcome == DecisionGateOutcome.BLOCK
    assert "is not in the operator's authorized agents list" in report_unauthorized_id.reason

    # Restore authorized agent for next check
    base_cognitive_state.operator_constraints.authorized_agents = ["agent_jules_sage"]

    # 2. Agent with UNAUTHORIZED authority level
    base_cognitive_state.agent_identity.authority_level = "UNAUTHORIZED"
    report_unauthorized_level = simulator.evaluate_decision(base_cognitive_state)
    assert report_unauthorized_level.outcome == DecisionGateOutcome.BLOCK
    assert "has invalid or unauthorized authority level" in report_unauthorized_level.reason


def test_confidence_state_recorded(base_cognitive_state):
    """Verify that the simulator records the confidence state accurately in the decision report."""
    simulator = PrefrontalCortexSimulator()

    # Test baseline confidence recording
    base_cognitive_state.confidence_state.overall_confidence = 0.95
    report = simulator.evaluate_decision(base_cognitive_state)
    assert report.confidence_recorded == 0.95

    # Test that confidence below 0.5 triggers REQUEST_CLARIFICATION
    base_cognitive_state.confidence_state.overall_confidence = 0.4
    low_confidence_report = simulator.evaluate_decision(base_cognitive_state)
    assert low_confidence_report.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION
    assert "Confidence level is too low" in low_confidence_report.reason
    assert low_confidence_report.confidence_recorded == 0.4
