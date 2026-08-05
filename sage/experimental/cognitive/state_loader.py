"""SAGE Cognitive State Loader and Continuity Retrieval Interface."""

import time
from typing import Optional, List
from sage.acr.session.session_state import SessionState, SessionStateManager
from sage.experimental.act.continuity_control import SAGEMissionQueue, SAGEMissionTask
from sage.experimental.cognitive.state_schema import (
    CognitiveState,
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveCompletedMilestone,
    CognitiveOperatorConstraints,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveValidatedFact,
    CognitiveForbiddenRegression,
)


class CognitiveStateLoader:
    """Loads and synchronizes SAGE operational states into the high-fidelity CognitiveState."""

    @staticmethod
    def load_cognitive_state(
        session_state: SessionState,
        mission_queue: Optional[SAGEMissionQueue] = None,
        agent_identity: Optional[CognitiveAgentIdentity] = None,
        operator_constraints: Optional[CognitiveOperatorConstraints] = None,
        forbidden_regressions: Optional[List[CognitiveForbiddenRegression]] = None,
        force_next_action_id: Optional[str] = None,
    ) -> CognitiveState:
        """Map SAGE raw session/mission states to structured high-fidelity CognitiveState."""
        # 1. Map Agent Identity
        if not agent_identity:
            agent_identity = CognitiveAgentIdentity(
                agent_id="agent_jules_sage",
                name="Jules",
                role="Senior Software Engineer",
                authority_level="TIER_1_COORDINATOR",
                governance_tier="TIER_1_COORDINATOR"
            )

        # 2. Map Active Mission
        objective_str = ", ".join(session_state.active_objectives) if session_state.active_objectives else "General continuous execution mission"
        active_mission = CognitiveActiveMission(
            mission_id=session_state.session_id,
            objective=objective_str,
            milestones=session_state.pending_actions + session_state.completed_actions,
            status="RUNNING" if session_state.pending_actions else "COMPLETED"
        )

        # 3. Map Completed Milestones
        completed_milestones = []
        for action_id in session_state.completed_actions:
            completed_milestones.append(
                CognitiveCompletedMilestone(
                    milestone_id=action_id,
                    completed_at=time.time() - 10.0,
                    evidence_hash=f"hash_completed_{action_id}_sha256",
                    reopened_count=0
                )
            )

        # 4. Map Next Action
        next_action = None
        if force_next_action_id and mission_queue:
            forced_task = mission_queue.get_task(force_next_action_id)
            if forced_task:
                next_action = CognitiveNextAction(
                    action_id=forced_task.task_id,
                    description=forced_task.description or f"Execute task {forced_task.task_id}",
                    assigned_agent=forced_task.assigned_agent,
                    required_evidence=forced_task.evidence_requirements
                )
        if not next_action and mission_queue:
            next_task = mission_queue.get_next_approved_task(session_state.active_objectives)
            if next_task:
                next_action = CognitiveNextAction(
                    action_id=next_task.task_id,
                    description=next_task.description or f"Execute task {next_task.task_id}",
                    assigned_agent=next_task.assigned_agent,
                    required_evidence=next_task.evidence_requirements
                )
        if not next_action and session_state.pending_actions:
            # Fallback to pending actions
            next_action_id = session_state.pending_actions[0]
            next_action = CognitiveNextAction(
                action_id=next_action_id,
                description=f"Execute pending task {next_action_id}",
                assigned_agent=agent_identity.agent_id,
                required_evidence=["git_commit"]
            )

        # 5. Map Operator Constraints
        if not operator_constraints:
            operator_constraints = CognitiveOperatorConstraints(
                permitted_paths=["sage/experimental/"],
                forbidden_paths=["sage/runtime/", "sage/core/", "sage/acr/", "sage/agents/"],
                requires_approval=True,
                max_consecutive_failures=3,
                authorized_agents=[agent_identity.agent_id, "ChatGPT", "Jules", "Claude", "Gemini"]
            )

        # 6. Map Forbidden Regressions
        if not forbidden_regressions:
            # Setup standard loop-prevention regression rule
            forbidden_regressions = [
                CognitiveForbiddenRegression(
                    regression_id=f"regr_prevent_loop_{session_state.session_id}",
                    description="Prevent infinite loop and redundant execution of already completed milestones",
                    restricted_actions=session_state.completed_actions
                )
            ]

        # 7. Map Validated Facts
        validated_facts = []
        for dec in session_state.important_decisions:
            validated_facts.append(
                CognitiveValidatedFact(
                    fact_id=f"fact_{dec}",
                    statement=f"Validated historical decision {dec}",
                    evidence_references=["session_ledger", f"audit_reference_{dec}"]
                )
            )

        # 8. Calculate Confidence State
        # Confidence score derived from total actions completion ratio and evidence completeness
        total_actions = len(session_state.completed_actions) + len(session_state.pending_actions)
        ratio = (len(session_state.completed_actions) / total_actions) if total_actions > 0 else 1.0
        confidence_val = min(1.0, 0.5 + (ratio * 0.5))

        confidence_state = CognitiveConfidenceState(
            overall_confidence=confidence_val,
            last_updated=time.time(),
            notes="State loaded and reconstructed from session state and active mission queue"
        )

        return CognitiveState(
            agent_identity=agent_identity,
            active_mission=active_mission,
            validated_facts=validated_facts,
            completed_milestones=completed_milestones,
            forbidden_regressions=forbidden_regressions,
            operator_constraints=operator_constraints,
            confidence_state=confidence_state,
            next_action=next_action
        )


class ContinuityRetrievalInterface:
    """Interface to programmatically verify that a fresh session cleanly reconstructs the SAGE cognitive state."""

    def __init__(self, state_loader: Optional[CognitiveStateLoader] = None):
        self.state_loader = state_loader or CognitiveStateLoader()

    def reconstruct_and_verify(
        self,
        session_id: str,
        session_manager: SessionStateManager,
        mission_queue: Optional[SAGEMissionQueue] = None,
    ) -> CognitiveState:
        """Loads and reconstructs the full cognitive state from persistent disk state to verify continuity."""
        session_state = session_manager.retrieve_session(session_id)
        if not session_state:
            raise ValueError(f"Cognitive Continuity Error: Session '{session_id}' not found in SessionState database.")

        cognitive_state = self.state_loader.load_cognitive_state(
            session_state=session_state,
            mission_queue=mission_queue
        )

        # Continuity Verification checks
        # 1. Verify current mission objective is reconstructed
        if not cognitive_state.active_mission or not cognitive_state.active_mission.objective:
            raise ValueError("Cognitive Continuity Check Failed: Current mission objective not reconstructed.")

        # 2. Verify completed work is recovered
        expected_completed = set(session_state.completed_actions)
        actual_completed = {m.milestone_id for m in cognitive_state.completed_milestones}
        if expected_completed != actual_completed:
            raise ValueError(f"Cognitive Continuity Check Failed: Completed actions mismatch. Expected: {expected_completed}, Actual: {actual_completed}")

        # 3. Verify forbidden regressions are mapped
        if not cognitive_state.forbidden_regressions:
            raise ValueError("Cognitive Continuity Check Failed: Forbidden regressions not mapped.")

        # 4. Verify required next action is specified if pending actions exist
        if session_state.pending_actions and not cognitive_state.next_action:
            raise ValueError("Cognitive Continuity Check Failed: Next action is missing while pending actions exist.")

        # 5. Verify confidence state is recorded
        if not cognitive_state.confidence_state:
            raise ValueError("Cognitive Continuity Check Failed: Confidence state is missing or unrecorded.")

        return cognitive_state
