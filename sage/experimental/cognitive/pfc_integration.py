"""SAGE Prefrontal Cortex Integration with existing SAGE Developer Workflow Orchestrator."""

import time
from typing import Dict, Any, Optional
from sage.experimental.act.continuity_control import DeveloperWorkflowOrchestrator, SAGEMissionTask
from sage.experimental.cognitive.state_schema import CognitiveState, CognitiveOperatorConstraints, CognitiveAgentIdentity
from sage.experimental.cognitive.state_loader import CognitiveStateLoader
from sage.experimental.cognitive.prefrontal_cortex import PrefrontalCortexSimulator, DecisionGateOutcome, PFCDecisionReport


class PFCGovernedExecutor:
    """Orchestrates Cognitive Context Loading, PFC evaluation, and safe execution routing."""

    def __init__(
        self,
        orchestrator: DeveloperWorkflowOrchestrator,
        simulator: Optional[PrefrontalCortexSimulator] = None,
        agent_identity: Optional[CognitiveAgentIdentity] = None,
        operator_constraints: Optional[CognitiveOperatorConstraints] = None,
    ):
        self.orchestrator = orchestrator
        self.simulator = simulator or PrefrontalCortexSimulator()
        self.agent_identity = agent_identity
        self.operator_constraints = operator_constraints

    def execute_governed_cycle(self, task_id: str) -> Dict[str, Any]:
        """Runs the complete integrated PFC-governed execution cycle for a specific task."""
        # 1. Context Load: Reconstruct the full high-fidelity CognitiveState
        # Retrieve the underlying SAGE SessionState
        session_state = self.orchestrator.session_manager.retrieve_session(self.orchestrator.session_id)
        if not session_state:
            session_state = self.orchestrator.session

        # Force the target task as the next pending action if not already there,
        # ensuring the state loader maps it to next_action.
        task = self.orchestrator.mission_queue.get_task(task_id)
        if task and task_id not in session_state.pending_actions and task_id not in session_state.completed_actions:
            session_state.add_pending_action(task_id)

        cognitive_state = CognitiveStateLoader.load_cognitive_state(
            session_state=session_state,
            mission_queue=self.orchestrator.mission_queue,
            agent_identity=self.agent_identity,
            operator_constraints=self.operator_constraints,
            force_next_action_id=task_id  # Force the loader to evaluate this specific task_id!
        )

        # 2. PFC Evaluation: Run the safety gates
        decision_report = self.simulator.evaluate_decision(cognitive_state)

        # 3. Handle Decision Outcomes
        execution_status = "NOT_EXECUTED"
        result_payload = {}
        error_message = None

        if decision_report.outcome == DecisionGateOutcome.PROCEED:
            # 4. Existing SAGE execution path: execute the actual task coordination
            execution_status = "EXECUTED"
            # Set active task ID on orchestrator
            self.orchestrator.active_task_id = task_id
            if task:
                task.status = "RUNNING"
                self.orchestrator.mission_queue.save_queue()

            try:
                # Trigger existing SAGE execution coordination path
                result_payload = self.orchestrator.execute_active_development_coordination(
                    action_taken=f"PFC PROCEED: Executing task {task_id}",
                    decision_reasoning=f"PFC evaluated PROCEED with confidence {decision_report.confidence_recorded}"
                )
                if task:
                    task.status = "COMPLETED"
                    self.orchestrator.mission_queue.save_queue()

                # Sync completed state
                self.orchestrator.session.add_completed_action(task_id)
                self.orchestrator.session_manager.save_session(self.orchestrator.session)

            except Exception as e:
                if task:
                    task.status = "FAILED"
                    self.orchestrator.mission_queue.save_queue()
                execution_status = "FAILED"
                error_message = str(e)

        elif decision_report.outcome == DecisionGateOutcome.BLOCK:
            execution_status = "BLOCKED"
            # Transition orchestrator mode to MANUAL_INTERVENTION_PAUSED on block to ensure safety alignment
            self.orchestrator.loop_state["mode"] = "MANUAL_INTERVENTION_PAUSED"
            self.orchestrator.save_loop_state()
            error_message = f"PFC BLOCKED execution: {decision_report.reason}"

        elif decision_report.outcome == DecisionGateOutcome.REQUEST_CLARIFICATION:
            execution_status = "REQUEST_CLARIFICATION"
            # Pause loop for safety
            self.orchestrator.loop_state["mode"] = "MANUAL_INTERVENTION_PAUSED"
            self.orchestrator.save_loop_state()
            error_message = f"PFC requested clarification: {decision_report.reason}"

        # Combine results
        return {
            "execution_status": execution_status,
            "decision_outcome": decision_report.outcome,
            "decision_reason": decision_report.reason,
            "confidence_recorded": decision_report.confidence_recorded,
            "checks_performed": decision_report.checks_performed,
            "orchestrator_result": result_payload,
            "error_message": error_message,
            "cognitive_state_dump": cognitive_state.model_dump()
        }
