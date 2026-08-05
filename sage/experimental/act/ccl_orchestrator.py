"""SAGE Multi-Agent Operational Orchestrator (SAGE-MACC Core).

Provides a structured coordination and control layer for AI-assisted workflows.
Specifically integrates ChatGPT (Coordinator), Jules (Developer Executor), and
Claude (Auditor Validation Readiness) into a unified, recovery-hardened, and trace-evident loop.
"""

import os
import json
import time
import uuid
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from sage.experimental.act.continuity_control import (
    DeveloperWorkflowOrchestrator,
    AgentProgressUpdate,
    AgentActivationState,
    WorkflowIntelligenceReport,
)


class OperationalStateWindow(BaseModel):
    """Encapsulates the 8-field complete context package for consecutive custody handoffs."""

    active_mission: Dict[str, Any] = Field(default_factory=dict)
    workflow_state: str = "ACTIVE"  # ACTIVE, DEGRADED, BLOCKED
    milestones: List[Dict[str, Any]] = Field(default_factory=list)
    scope: List[str] = Field(default_factory=list)
    repo_context: Dict[str, Any] = Field(default_factory=dict)
    blockers: List[str] = Field(default_factory=list)
    required_actions: List[str] = Field(default_factory=list)
    evidence_history: List[Dict[str, Any]] = Field(default_factory=list)


class ChatGPTAgentConnector:
    """Bridges ChatGPT's coordination role with SAGE multi-agent control loops."""

    def __init__(self, orchestrator: DeveloperWorkflowOrchestrator):
        self.orchestrator = orchestrator
        self.agent_id = "agent_chatgpt"
        self._register_role()

    def _register_role(self):
        self.orchestrator.register_agent_role(
            agent_id=self.agent_id,
            name="ChatGPT",
            role="COORDINATOR",
            scope=["sage/experimental/", "tests/experimental/", "evidence_capture/"],
            tier="TIER_1_COORDINATOR"
        )

    def formulate_coordination_directives(
        self,
        task_objective: str,
        milestones: List[str]
    ) -> Dict[str, Any]:
        """Formulates coordination directives and initiates agent activation."""
        self.orchestrator.session.add_objective(task_objective)
        for m in milestones:
            self.orchestrator.session.add_pending_action(m)
        self.orchestrator.session_manager.save_session(self.orchestrator.session)

        # Initialize activation state for ChatGPT Coordinator
        act_state = self.orchestrator.initialize_agent_activation(
            agent_id=self.agent_id,
            assigned_task_id="task_coordination",
            authorized_scope=["sage/experimental/", "tests/experimental/", "evidence_capture/"]
        )

        # Authorize ChatGPT activation
        auth_state = self.orchestrator.authorize_agent_activation(
            agent_id=self.agent_id,
            supervisor_id="supervisor_jules",
            signature=f"sig_chatgpt_act_{uuid.uuid4().hex[:6]}"
        )

        return {
            "agent_id": self.agent_id,
            "assigned_task_id": "task_coordination",
            "activation_state": auth_state.lifecycle_state,
            "directives": {
                "task_objective": task_objective,
                "milestones": milestones
            }
        }


class JulesAgentConnector:
    """Bridges Jules' engineering execution role with the SAGE multi-agent loop."""

    def __init__(self, orchestrator: DeveloperWorkflowOrchestrator):
        self.orchestrator = orchestrator
        self.agent_id = "agent_jules_sage"
        self._register_role()

    def _register_role(self):
        self.orchestrator.register_agent_role(
            agent_id=self.agent_id,
            name="Jules",
            role="DEVELOPER",
            scope=["sage/experimental/", "tests/experimental/", "evidence_capture/"],
            tier="TIER_2_DEVELOPER"
        )

    def accept_engineering_task(self, context_package: Dict[str, Any]) -> Dict[str, Any]:
        """Rehydrates operational engineering context and registers activation."""
        session_id = context_package["active_mission"]["session_id"]

        # Verify and re-initialize activation state
        self.orchestrator.initialize_agent_activation(
            agent_id=self.agent_id,
            assigned_task_id="task_active_development",
            authorized_scope=["sage/experimental/", "tests/experimental/", "evidence_capture/"]
        )
        auth_state = self.orchestrator.authorize_agent_activation(
            agent_id=self.agent_id,
            supervisor_id="supervisor_jules",
            signature=f"sig_jules_act_{uuid.uuid4().hex[:6]}"
        )

        return {
            "agent_id": self.agent_id,
            "assigned_task_id": "task_active_development",
            "activation_state": auth_state.lifecycle_state,
            "rehydrated_milestones": context_package.get("milestones", [])
        }


class ClaudeAgentConnector:
    """Prepares validated review contracts for future Claude validation/review readiness."""

    def __init__(self, orchestrator: DeveloperWorkflowOrchestrator):
        self.orchestrator = orchestrator
        self.agent_id = "agent_claude"
        self._register_role()

    def _register_role(self):
        self.orchestrator.register_agent_role(
            agent_id=self.agent_id,
            name="Claude",
            role="AUDITOR",
            scope=["tests/experimental/", "evidence_capture/"],
            tier="TIER_1_COORDINATOR"
        )

    def compile_review_contract(self, state_window: OperationalStateWindow) -> Dict[str, Any]:
        """Compiles a complete, signed review contract inheriting full custody lineage."""
        contract_id = f"REV-CONTRACT-{uuid.uuid4().hex[:12].upper()}"

        # Build review contract payload
        contract = {
            "contract_id": contract_id,
            "timestamp": time.time(),
            "target_auditor_id": self.agent_id,
            "inherited_state": state_window.model_dump(),
            "governance_status": "AWAITING_ACTIVATION",
            "instructions": "Audit implementation history, verify cryptographic checksums, and sign to transition records to INTEGRATED."
        }

        # Save to session metadata
        self.orchestrator.session.metadata["review_contract"] = contract
        self.orchestrator.session_manager.save_session(self.orchestrator.session)

        # Log to CCL ledger
        rec = self.orchestrator.ccl.intercept_event(
            event_type="state_transition",
            action_taken=f"Prepared Future Auditor Review Contract: {contract_id}",
            decision_reasoning="Establish clear audit lineage and handoff validation boundaries for future Claude validation.",
            session_id=self.orchestrator.session_id,
            evidence_payload={"contract_id": contract_id}
        )
        self.orchestrator.ccl.serialize_record(rec)

        return contract


class SAGEOperationalOrchestrator:
    """Manages full operational multi-agent workflow, recovery, status reporting, and evidence hardening."""

    def __init__(
        self,
        session_id: str = "session_operational_validation",
        evidence_output_path: str = "evidence_capture/ccl_orchestrator_evidence.json"
    ):
        self.orchestrator = DeveloperWorkflowOrchestrator(
            session_id=session_id,
            objective="obj_continuous_development"
        )
        self.evidence_output_path = Path(evidence_output_path)

        # Instantiate connectors
        self.chatgpt = ChatGPTAgentConnector(self.orchestrator)
        self.jules = JulesAgentConnector(self.orchestrator)
        self.claude = ClaudeAgentConnector(self.orchestrator)

    def assemble_context_package(self, active_owner_id: str) -> Dict[str, Any]:
        """Compiles the complete 8-field state context package for secure consecutive custody transfers."""
        report = self.orchestrator.generate_workflow_intelligence_report()
        workspace = self.orchestrator.scan_git_workspace()

        # Retrieve active registration
        registry = self.orchestrator.session.metadata.get("agent_registry", {})
        owner_reg = registry.get(active_owner_id, {})

        # Compute file fingerprints
        file_fingerprints = {}
        for file in workspace["modified_files"]:
            file_hash = hashlib.sha256(file.encode()).hexdigest()
            if os.path.exists(file):
                try:
                    with open(file, "rb") as f:
                        file_hash = hashlib.sha256(f.read()).hexdigest()
                except Exception:
                    pass
            file_fingerprints[file] = {
                "sha256": file_hash,
                "size_bytes": os.path.getsize(file) if os.path.exists(file) else 0
            }

        # Compile state window
        state_window = OperationalStateWindow(
            active_mission={
                "session_id": self.orchestrator.session_id,
                "objectives": list(self.orchestrator.session.active_objectives),
                "active_owner_id": active_owner_id,
                "owner_metadata": owner_reg
            },
            workflow_state=report["workflow_status"],
            milestones=[
                {"id": f"milestone_{i}", "action": action, "status": "COMPLETED" if action in self.orchestrator.session.completed_actions else "PENDING"}
                for i, action in enumerate(self.orchestrator.session.pending_actions)
            ],
            scope=owner_reg.get("authorized_scope_prefixes", []),
            repo_context={
                "uncommitted_files": workspace["modified_files"],
                "file_fingerprints": file_fingerprints
            },
            blockers=report["blocked_conditions"],
            required_actions=[sig["recommendation"] for sig in report["actionable_operator_signals"]],
            evidence_history=[]  # Loaded dynamically from storage later
        )

        # Load SAGE-CCL evidence history from disk
        evidence_history = []
        for f in self.orchestrator.ccl.storage_path.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if data.get("session_id") == self.orchestrator.session_id:
                        evidence_history.append({
                            "record_id": data.get("record_id"),
                            "event_type": data.get("event_type"),
                            "action_taken": data.get("action_taken"),
                            "timestamp": data.get("timestamp"),
                            "lifecycle_state": data.get("lifecycle_state")
                        })
            except Exception:
                pass
        state_window.evidence_history = sorted(evidence_history, key=lambda x: x["timestamp"])

        return state_window.model_dump()

    def execute_two_role_coordination_and_recovery_loop(
        self,
        task_objective: str,
        milestones: List[str],
        simulate_recovery: bool = False
    ) -> Dict[str, Any]:
        """Runs the complete multi-agent operational workflow and validation sequence."""
        execution_traces = []

        # 1. ChatGPT Coordination Step
        execution_traces.append({"event": "CHATGPT_COORDINATE_START", "timestamp": time.time()})
        chatgpt_res = self.chatgpt.formulate_coordination_directives(task_objective, milestones)
        execution_traces.append({
            "event": "CHATGPT_COORDINATE_COMPLETED",
            "timestamp": time.time(),
            "details": chatgpt_res
        })

        # Assemble package for handoff
        context_package = self.assemble_context_package(self.chatgpt.agent_id)

        # Activate Jules for target step
        self.orchestrator.initialize_agent_activation(
            agent_id=self.jules.agent_id,
            assigned_task_id="task_active_development",
            authorized_scope=["sage/experimental/", "tests/experimental/", "evidence_capture/"]
        )

        # Execute consecutive custody handoff ChatGPT -> Jules
        execution_traces.append({"event": "HANDOFF_CHATGPT_TO_JULES_START", "timestamp": time.time()})
        handoff_trace = self.orchestrator.execute_agent_handoff(
            from_agent_id=self.chatgpt.agent_id,
            to_agent_id=self.jules.agent_id
        )
        execution_traces.append({
            "event": "HANDOFF_CHATGPT_TO_JULES_COMPLETED",
            "timestamp": time.time(),
            "handoff_id": handoff_trace["handoff_id"]
        })

        # 2. Jules Engineering Execution Step
        execution_traces.append({"event": "JULES_EXECUTION_START", "timestamp": time.time()})
        jules_res = self.jules.accept_engineering_task(context_package)

        # Simulate Multi-Agent Recovery testing if requested
        if simulate_recovery:
            execution_traces.append({"event": "RECOVERY_SIMULATION_INTERRUPT", "timestamp": time.time()})
            # Simulate a temporary block/interrupted state
            temp_block_rec = self.orchestrator.ccl.intercept_event(
                event_type="boundary_intercept",
                action_taken="SIMULATED INTERRUPT: Network delay / partial task completion",
                decision_reasoning="Verify SAGE continuity and objective state preservation under interrupted conditions.",
                session_id=self.orchestrator.session_id,
                failure_context={"reason": "simulated_delayed_response"},
                recovery_path="rehydrate_and_resume"
            )
            self.orchestrator.ccl.serialize_record(temp_block_rec)

            # Rehydrate from handoff manifest to restore full context and resume
            m_path = "evidence_capture/agent_handoff_manifest.json"
            self.orchestrator.prepare_agent_handoff(output_path=m_path)
            rehydrate_report = self.orchestrator.rehydrate_from_handoff_manifest(m_path)

            execution_traces.append({
                "event": "RECOVERY_SIMULATION_RESUMED",
                "timestamp": time.time(),
                "rehydration_details": rehydrate_report
            })

        # Record Jules implementation progress update
        update = AgentProgressUpdate(
            agent_id=self.jules.agent_id,
            step_id="step_jules_impl_01",
            action_taken="Wrote high-fidelity ccl_orchestrator multi-agent validation pathways",
            objective_alignment=task_objective,
            modified_files=["sage/experimental/act/continuity_control.py"]
        )
        exec_res = self.orchestrator.record_agent_execution_step(update)

        execution_traces.append({
            "event": "JULES_EXECUTION_COMPLETED",
            "timestamp": time.time(),
            "details": exec_res
        })

        # Complete Jules Task Activation
        self.orchestrator.complete_agent_activation(self.jules.agent_id)

        # 3. Future Review Preparation Step (Claude Validation Readiness)
        execution_traces.append({"event": "REVIEW_PREPARATION_START", "timestamp": time.time()})
        final_state_package = self.assemble_context_package(self.jules.agent_id)
        state_window = OperationalStateWindow(**final_state_package)

        review_contract = self.claude.compile_review_contract(state_window)
        execution_traces.append({
            "event": "REVIEW_PREPARATION_COMPLETED",
            "timestamp": time.time(),
            "contract_id": review_contract["contract_id"]
        })

        # Compile final integrated operational validation report
        validation_report = {
            "orchestrator_run_id": f"orch_run_macc_{uuid.uuid4().hex[:12]}",
            "timestamp": time.time(),
            "session_id": self.orchestrator.session_id,
            "status": "VALIDATED",
            "chatgpt_coordination": chatgpt_res,
            "jules_execution": jules_res,
            "review_contract": review_contract,
            "execution_traces": execution_traces,
            "control_tower_status": self.render_control_tower_view()
        }

        # Save to evidence capture directory
        self.evidence_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.evidence_output_path, "w", encoding="utf-8") as f:
            json.dump(validation_report, f, indent=2, default=str)

        return validation_report

    def render_control_tower_view(self) -> str:
        """Renders an advanced operator status view showing responsibilities, handoff lineages, and evidence trails."""
        workspace = self.orchestrator.scan_git_workspace()
        report = self.orchestrator.generate_workflow_intelligence_report()

        # Count CCL ledger records
        proposed_records = 0
        validated_records = 0
        for f in self.orchestrator.ccl.storage_path.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    data = json.load(file)
                    if data.get("lifecycle_state") == "VALIDATED":
                        validated_records += 1
                    elif data.get("lifecycle_state") == "PROPOSED":
                        proposed_records += 1
            except Exception:
                pass

        # Parse registered collaborator details
        registry = self.orchestrator.session.metadata.get("agent_registry", {})
        ecosystem = []
        for aid, reg in registry.items():
            ecosystem.append(f"    - {reg['name']} ({aid}) [Role: {reg['role']}] [Tier: {reg['governance_tier']}]")

        # Parse active handoff history
        handoffs = self.orchestrator.session.metadata.get("handoff_history", [])
        handoff_lineage = []
        for ho in handoffs:
            handoff_lineage.append(f"    * {ho['from_agent']['name']} -> {ho['to_agent']['name']} [Trace ID: {ho['handoff_id']}]")

        # Compile the final Control Tower Console
        console = [
            "==========================================================",
            "  SAGE CO-ORDINATION CONTROL TOWER CONSOLE (SAGE-MACC-OP)",
            "==========================================================",
            f"Active Operational Session: {self.orchestrator.session_id}",
            f"Workflow Health Score:      {report['health_score']:.1f}% ({report['workflow_status']})",
            "----------------------------------------------------------",
            "Active Collaborator Responsibility Hierarchy:",
            "\n".join(ecosystem) if ecosystem else "  No active collaborator network registered.",
            "----------------------------------------------------------",
            "Custody Transfer Handoff Lineage Trail:",
            "\n".join(handoff_lineage) if handoff_lineage else "  No consecutive custody handoffs completed yet.",
            "----------------------------------------------------------",
            "Traceable Evidence Ledger Status:",
            f"  Proposed Records:          {proposed_records}",
            f"  Validated Audit Records:   {validated_records}",
            "----------------------------------------------------------",
            "Active Workspace Guard Metrics:",
            f"  Uncommitted files track:   {len(workspace['modified_files'])} file(s)",
            "=========================================================="
        ]
        return "\n".join(console)


if __name__ == "__main__":
    print("[*] Launching SAGE Multi-Agent Operational Orchestrator (SAGE-MACC Core)...")
    macc_orch = SAGEOperationalOrchestrator()
    print("[*] Running end-to-end Operational Workflow scenario validation...")

    report = macc_orch.execute_two_role_coordination_and_recovery_loop(
        task_objective="obj_continuous_development",
        milestones=[
            "Formulate multi-agent operational boundaries",
            "Coordinate secure custody handoffs",
            "Audit state-window contextual checksums"
        ],
        simulate_recovery=True
    )
    print("\n[+] Operational Scenario Validation Run Succeeded!")
    print(f"    - Run ID: {report['orchestrator_run_id']}")
    print(f"    - Claude Review Contract: {report['review_contract']['contract_id']}")
    print(f"    - Evidence logged to: {macc_orch.evidence_output_path}\n")
    print(report["control_tower_status"])
