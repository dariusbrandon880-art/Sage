"""Prefrontal Cortex (PFC) Simulator for SAGE Cognitive Kernel."""

from enum import Enum
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from sage.experimental.cognitive.state_schema import CognitiveState


class DecisionGateOutcome(str, Enum):
    """Outcomes from the PFC decision gate."""

    PROCEED = "PROCEED"
    BLOCK = "BLOCK"
    REQUEST_CLARIFICATION = "REQUEST_CLARIFICATION"


class PFCDecisionReport(BaseModel):
    """Structured report returned by the PFC decision gate."""

    outcome: DecisionGateOutcome
    reason: str
    confidence_recorded: float
    checks_performed: Dict[str, bool] = Field(default_factory=dict)


class PrefrontalCortexSimulator:
    """Simulates prefrontal cortex executive control of cognitive state transitions."""

    def evaluate_decision(self, state: CognitiveState) -> PFCDecisionReport:
        """Evaluate cognitive state and proposed next action against safety gates."""
        checks_performed = {
            "mission_alignment": False,
            "completed_work_protection": False,
            "constraint_validation": False,
            "evidence_requirement_detection": False,
        }

        # Handle missing proposed next action
        if not state.next_action:
            checks_performed["mission_alignment"] = True
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.REQUEST_CLARIFICATION,
                reason="No next action proposed in the active cognitive state.",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        next_action = state.next_action

        # Check for missing/blank fields (missing context)
        if not next_action.action_id or not next_action.description.strip():
            checks_performed["mission_alignment"] = True
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.REQUEST_CLARIFICATION,
                reason="Proposed action is missing crucial context (action_id or description is empty).",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        # 1. Constraint Validation (including authority check)
        checks_performed["constraint_validation"] = True
        # Check authorization of the agent
        authorized_agents = state.operator_constraints.authorized_agents
        if authorized_agents and state.agent_identity.agent_id not in authorized_agents:
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.BLOCK,
                reason=f"Agent '{state.agent_identity.agent_id}' is not in the operator's authorized agents list.",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        # Reject actions with unauthorized or invalid authority levels / governance tiers
        if state.agent_identity.authority_level == "UNAUTHORIZED" or state.agent_identity.governance_tier == "UNTRUSTED":
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.BLOCK,
                reason=f"Agent '{state.agent_identity.name}' has invalid or unauthorized authority level/governance tier.",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        # 2. Completed-Work Protection
        checks_performed["completed_work_protection"] = True
        completed_milestone_ids = {m.milestone_id for m in state.completed_milestones}
        if next_action.action_id in completed_milestone_ids:
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.BLOCK,
                reason=f"Completed milestone reopening/modification blocked for milestone '{next_action.action_id}'.",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        # 3. Mission Alignment
        checks_performed["mission_alignment"] = True
        # Check alignment of action against mission objective/milestones
        mission = state.active_mission
        if mission.status == "COMPLETED":
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.BLOCK,
                reason="Cannot propose actions for an already completed mission.",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        # Check keyword/semantic overlap for mission alignment
        if not mission.objective.strip():
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.REQUEST_CLARIFICATION,
                reason="Active mission objective is undefined or empty.",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        # Simple keyword alignment test
        objective_words = set(w.lower() for w in mission.objective.split())
        action_words = set(w.lower() for w in next_action.description.split())
        overlap = objective_words.intersection(action_words)
        # If there's zero overlap and objective/action descriptions are non-empty, request clarification
        if not overlap and len(objective_words) > 1 and len(action_words) > 1:
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.REQUEST_CLARIFICATION,
                reason=f"Proposed action '{next_action.action_id}' does not semantically align with the active mission objective.",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        # 4. Evidence Requirement Detection
        checks_performed["evidence_requirement_detection"] = True
        # If confidence state overall_confidence is too low, request clarification
        if state.confidence_state.overall_confidence < 0.5:
            return PFCDecisionReport(
                outcome=DecisionGateOutcome.REQUEST_CLARIFICATION,
                reason=f"Confidence level is too low ({state.confidence_state.overall_confidence}) to proceed without operator review.",
                confidence_recorded=state.confidence_state.overall_confidence,
                checks_performed=checks_performed,
            )

        # If next action has required evidence but state has no validated facts referencing it, request clarification
        if next_action.required_evidence:
            fact_evidence_refs = set()
            for fact in state.validated_facts:
                fact_evidence_refs.update(fact.evidence_references)

            missing_evidence = [req for req in next_action.required_evidence if req not in fact_evidence_refs]
            if missing_evidence:
                return PFCDecisionReport(
                    outcome=DecisionGateOutcome.REQUEST_CLARIFICATION,
                    reason=f"Proposed action requires evidence references {missing_evidence} which are missing from validated facts.",
                    confidence_recorded=state.confidence_state.overall_confidence,
                    checks_performed=checks_performed,
                )

        # All gates passed successfully!
        return PFCDecisionReport(
            outcome=DecisionGateOutcome.PROCEED,
            reason="Proposed next action aligns with active mission, passes constraint checks, respects completed milestones, and possesses required evidence.",
            confidence_recorded=state.confidence_state.overall_confidence,
            checks_performed=checks_performed,
        )
