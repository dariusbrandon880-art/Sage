#!/usr/bin/env python
"""Script to run the end-to-end governed safety-gated execution loop.

Exercises both a safe cognitive state pipeline and an unsafe block pipeline,
printing the beautiful Operator Control Tower summary dynamically.
"""

import os
from sage.experimental.mission_control_bridge import SAGEMissionExecutionBridge
from sage.experimental.cognitive.state_schema import (
    CognitiveState,
    CognitiveAgentIdentity,
    CognitiveActiveMission,
    CognitiveConfidenceState,
    CognitiveNextAction,
    CognitiveOperatorConstraints,
)


def run_governed_loops():
    bridge = SAGEMissionExecutionBridge()
    modified_files = ["tests/test_continuity_bridge.py"]

    # 1. Safe Cognitive State Execution
    print("\n--- STARTING 1. SAFE COGNITIVE STATE WORKFLOW ---")
    safe_report = bridge.execute_workspace_pipeline(
        modified_files=modified_files,
        mission_id="msn-safe-execution-run-01",
        lineage_output_path="evidence_capture/safety_gated_execution_evidence.json"
    )

    # 2. Unsafe/Blocked Cognitive State Execution
    print("\n--- STARTING 2. UNSAFE COGNITIVE STATE WORKFLOW ---")
    agent = CognitiveAgentIdentity(
        agent_id="agent_jules_sage",
        name="Jules",
        role="Senior Software Engineer",
        authority_level="TIER_1_COORDINATOR",
        governance_tier="TIER_1_COORDINATOR",
    )
    mission = CognitiveActiveMission(
        mission_id="msn-unsafe-execution-run-01",
        objective="Verify continuous integration revalidation paths on workspace changes",
        status="RUNNING"
    )
    constraints = CognitiveOperatorConstraints(
        authorized_agents=["agent_jules_sage"]
    )
    # Low confidence triggers REQUEST_CLARIFICATION safety block
    confidence = CognitiveConfidenceState(
        overall_confidence=0.1,
        last_updated=0.0
    )
    next_action = CognitiveNextAction(
        action_id="task_workspace_revalidation",
        description="Verify integration paths on workspace changes",
        assigned_agent="agent_jules_sage"
    )
    unsafe_state = CognitiveState(
        agent_identity=agent,
        active_mission=mission,
        operator_constraints=constraints,
        confidence_state=confidence,
        next_action=next_action
    )

    unsafe_report = bridge.execute_workspace_pipeline(
        modified_files=modified_files,
        mission_id="msn-unsafe-execution-run-01",
        cognitive_state=unsafe_state,
        lineage_output_path="evidence_capture/safety_gated_execution_evidence.json"
    )


if __name__ == "__main__":
    run_governed_loops()
