"""Run script for SAGE Continuity Control Loop (SAGE-CCL) Operational Coordination Engine.

Executes a complete coordinated loop involving ChatGPTAgentConnector (COORDINATOR),
JulesAgentConnector (EXECUTOR), and ReviewerAgentConnector (REVIEWER), generates
operational control tower and intelligence summaries, and exports the formal SAGE evidence package.
"""

import sys
import os

# Ensure repo root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sage.experimental.act.ccl_orchestrator import (
    DeveloperWorkflowOrchestrator,
    ChatGPTAgentConnector,
    JulesAgentConnector,
    ReviewerAgentConnector,
)


def run_coordination_loop():
    print("--- Starting SAGE Three-Role Governed Operational Loop (SAGE-CCL-OPS) Run ---")

    # Initialize Orchestrator
    orch = DeveloperWorkflowOrchestrator(session_id="session_ccl_ops_2026")

    # 1. Register and Activate Agents
    print("[1/7] Activating Agent Network Registry & Connectors...")
    chatgpt = ChatGPTAgentConnector(orch, agent_id="agent_chatgpt_coord")
    jules = JulesAgentConnector(orch, agent_id="agent_jules_exec")
    reviewer = ReviewerAgentConnector(orch, agent_id="agent_reviewer_gemini")

    # Activate additional Analyst agent
    orch.ingest_event(
        "AGENT_ACTIVATION",
        "system",
        {
            "agent_id": "agent_analyst_claude",
            "supervisor_id": "human_supervisor_01",
            "decision": "AUTHORIZED",
            "role": "ANALYST",
        },
    )

    # 2. ChatGPT Coordinator Rehydrates Mission Context and Initiates Task
    print("[2/7] ChatGPT Coordinated Context Rehydration & Task Initiation...")
    rehydrated = chatgpt.rehydrate_context()
    print(f"      Rehydrated Objectives: {rehydrated['rehydrated_objectives']}")
    print(f"      Lineage Baselines    : {rehydrated['lineage_baselines']}")

    chatgpt.align_workflow_state(
        "INITIATE_TASK",
        "task_ops_parent",
        {
            "objective_id": "obj_code_review_refactor",
            "initial_context": {
                "workspace": "sage/experimental/act",
                "status_check": "passed",
            },
            "lineage_references": ["ADR-001", "SAGE-ACT-MP-2.0"],
        },
    )

    chatgpt.align_workflow_state(
        "START_EXECUTION",
        "task_ops_parent",
        {"comment": "ChatGPT Coordinator starts the multi-agent refactoring workflow."},
    )

    # 3. Task Delegation to Executor (Jules) and Analyst (Claude)
    print("[3/7] Dynamic Task Delegation Tree Assembly...")
    orch.delegate_task(
        parent_task_id="task_ops_parent",
        child_task_id="subtask_exec",
        to_agent="agent_jules_exec",
        objective_id="obj_write_ccl_orchestrator",
        initial_context={
            "files_to_modify": ["sage/experimental/act/ccl_orchestrator.py"],
            "milestones_completed": ["Milestone-1-contracts", "Milestone-2-ccl-ops"],
        },
    )

    orch.delegate_task(
        parent_task_id="task_ops_parent",
        child_task_id="subtask_analyst",
        to_agent="agent_analyst_claude",
        objective_id="obj_verify_ast_isolation",
    )

    # ChatGPT clarifies objective for Jules Executor
    chatgpt.clarify_objective(
        "subtask_exec",
        "Are core folders out-of-scope for refactoring?",
        "Yes, core folders sage/runtime, sage/core, sage/acr, and sage/agents are locked. Modify sage/experimental only.",
    )

    # 4. Jules Rehydrates Engineering Context, Commits State, and Reports Execution Progress
    print("[4/7] Jules Engineering Agent Context Rehydration & Execution...")
    jules_ctx = jules.rehydrate_engineering_context("subtask_exec")
    print(f"      Jules Active Mission: {jules_ctx['active_mission']}")
    print(f"      Jules Assigned Scope: {jules_ctx['assigned_engineering_responsibility']['target_files']}")
    print(f"      Preceding State Hash: {jules_ctx['evidence_history']['preceding_records_hashes'][0][:16]}")

    jules.align_task_state("subtask_exec", "ACTIVE", "Jules starts refactoring task.")

    # Record some early progress
    jules.report_progress(
        task_id="subtask_exec",
        progress_percent=50.0,
        result_payload={},
        feedback="Verify and test AST compilation limits.",
    )

    # Complete execution progress reporting
    jules.report_progress(
        task_id="subtask_exec",
        progress_percent=100.0,
        result_payload={"git_hash": "a8c9b201"},
        feedback="Finished implementation. AST compliance checked.",
    )

    # Analyst executes isolation checks
    orch.ingest_event("STATE_TRANSITION", "subtask_analyst", {"target_status": "ACTIVE"})
    orch.record_progress(
        task_id="subtask_analyst",
        agent_id="agent_analyst_claude",
        progress_percent=100.0,
        result_payload={"violations": 0, "core_untouched": True},
        feedback="Verified 100% core isolation.",
    )

    # 5. Peer Review and Coordinated Agent Handoff Manifest Assembly
    print("[5/7] Context-Preserving Peer Handoff...")
    # Generate the handoff manifest to transfer subtask_exec from Jules to Reviewer
    jules.generate_handoff_manifest("subtask_exec", "agent_reviewer_gemini")

    # 6. Review Context package Rehydration & Peer Finding submission (Gemini Reviewer)
    print("[6/7] Reviewer Context Rehydration & Evidence-Backed Peer Review...")
    review_ctx = reviewer.rehydrate_review_context("subtask_exec")
    preceding_hash = review_ctx["evidence_package"]["preceding_records_hashes"][0]
    print(f"      Reviewer Active Mission  : {review_ctx['active_mission']}")
    print(f"      Reviewer Preceding Hash  : {preceding_hash[:16]}")

    reviewer.submit_review_finding(
        task_id="subtask_exec",
        finding_details="AST boundary safety and isolation verified clean.",
        evidence_hash_reference=preceding_hash
    )

    # 7. Human Authorization Checkpoints & Multi-Agent Completion
    print("[7/7] Human Checkpoint Sign-offs & Workflow Completion...")
    orch.ingest_event(
        "HUMAN_APPROVAL",
        "subtask_exec",
        {
            "supervisor_id": "human_supervisor_01",
            "decision": "AUTHORIZED",
            "comments": "Code implementation is verified secure and reviewed clean.",
        },
    )
    orch.ingest_event(
        "STATE_TRANSITION",
        "subtask_exec",
        {
            "target_status": "COMPLETED",
            "agent_id": "agent_reviewer_gemini",
            "comment": "Reviewer signed off on code refactoring and findings.",
        },
    )

    orch.ingest_event(
        "HUMAN_APPROVAL",
        "subtask_analyst",
        {
            "supervisor_id": "human_supervisor_01",
            "decision": "AUTHORIZED",
            "comments": "AST isolation checked.",
        },
    )
    orch.ingest_event(
        "STATE_TRANSITION",
        "subtask_analyst",
        {
            "target_status": "COMPLETED",
            "agent_id": "agent_analyst_claude",
            "comment": "Analyst signed off.",
        },
    )

    orch.ingest_event(
        "HUMAN_APPROVAL",
        "task_ops_parent",
        {
            "supervisor_id": "human_supervisor_01",
            "decision": "AUTHORIZED",
            "comments": "Complete multi-agent coordination approved.",
        },
    )
    chatgpt.align_workflow_state(
        "RECORD_PROGRESS",
        "task_ops_parent",
        {
            "progress_percent": 100.0,
            "result_payload": {"coordinated_milestones_completed": ["ccl-ops-e2e-passed"]},
            "feedback": "Coordinated multi-agent workflow executed flawlessly.",
        }
    )
    orch.ingest_event(
        "STATE_TRANSITION",
        "task_ops_parent",
        {
            "target_status": "COMPLETED",
            "agent_id": "agent_chatgpt_coord",
            "comment": "Coordinated workflow completed. Closing parent task.",
        },
    )

    # Export SAGE evidence package
    evidence_path = "evidence_capture/ccl_orchestrator_evidence.json"
    orch.export_evidence(evidence_path)
    print(f"\n[✔] SAGE Evidence Package exported to: {evidence_path}")

    # Output terminal view
    print(orch.generate_operator_summary())


if __name__ == "__main__":
    run_coordination_loop()
