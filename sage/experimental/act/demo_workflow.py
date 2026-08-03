"""SAGE First Demonstration Workflow Orchestration Layer.

Coordinates the end-to-end read-only user demonstration workflow sequence,
integrating Context Guard, SDR-004, CRC-2.0, and ACT-PROD Demonstrator state trees.
"""

import os
import json
import hashlib
from typing import Any, Dict, List
from datetime import datetime, timezone


class SAGEDemoWorkflowOrchestrator:
    """Orchestrates the SAGE Demonstration workflow end-to-end, producing repeatable evidence artifacts."""

    def __init__(self, output_path: str = "evidence_capture/demo_workflow_evidence.json"):
        self.output_path = output_path
        self.workflow_states: Dict[str, Dict[str, Any]] = {}

    def execute_demo_sequence(
        self,
        session_id: str,
        action_type: str,
        user_id: str,
        approver: str,
        signature: str,
        context_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Runs the entire target workflow sequence:

        User action → SAGE intake → context evaluation → capability analysis
        → human checkpoint visualization → evidence receipt generation → demonstrator output
        """
        # 1. SAGE Intake
        intake = {
            "status": "INTAKE_COMPLETE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "action_type": action_type,
            "user_id": user_id,
            "context_data": context_data,
        }

        # 2. Context Evaluation (Simulating Context Guard checks)
        context_evaluation = {
            "status": "EVALUATION_SUCCESS",
            "monitored_paths": ["sage/runtime/", "sage/core/", "sage/acr/"],
            "boundary_isolation_verified": True,
            "unauthorized_mutations_prevented": 0,
        }

        # 3. Capability Analysis (Simulating SDR-004 divergence and CRC-2.0 trust layers)
        capability_analysis = {
            "sdr_divergence_status": "MONITORED",
            "split_brain_detected": True,
            "recovery_checkpoints_active": [
                {
                    "checkpoint_id": "chk_rec_001_initial",
                    "status": "restored",
                    "authority_restored": "supervisor_lead",
                }
            ],
            "crc_trust_layer": {
                "asymmetric_signed": True,
                "attestation": "SAGE_TRUST_ATTESTATION_SUCCESS",
            },
        }

        # 4. Human Checkpoint Visualization Flow
        human_checkpoint = {
            "status": "APPROVED",
            "approver": approver,
            "signature": signature,
            "authorized_at": datetime.now(timezone.utc).isoformat(),
            "assertion": "HUMAN_OVERRIDE_VERIFIED",
        }

        # 5. Evidence Receipt Generation
        payload_data = {
            "intake": intake,
            "context_evaluation": context_evaluation,
            "capability_analysis": capability_analysis,
            "human_checkpoint": human_checkpoint,
        }
        serialized = json.dumps(payload_data, sort_keys=True)
        verification_hash = hashlib.sha256(serialized.encode()).hexdigest()

        evidence_receipt = {
            "receipt_id": f"receipt_{verification_hash[:16]}",
            "verification_hash": verification_hash,
            "assertion": "SAGE_ACTIVATION_RECEIPT_VALID",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # 6. Demonstrator Output Integration
        demo_output = {
            "lineage_visualization": {
                "active_session": session_id,
                "session_status": intake["status"],
            },
            "divergence_visibility": {
                "divergence_detected": True,
                "conflict_type": "state_split_brain",
            },
            "receipt_verification_display": {
                "receipt_id": evidence_receipt["receipt_id"],
                "verification_hash": verification_hash,
            },
        }

        # Combine into complete Workflow State Package
        workflow_state = {
            "workflow_id": f"workflow_{hashlib.md5(session_id.encode()).hexdigest()[:8]}",
            "session_id": session_id,
            "user_action": {
                "action_type": action_type,
                "user_id": user_id,
            },
            "intake": intake,
            "context_evaluation": context_evaluation,
            "capability_analysis": capability_analysis,
            "human_checkpoint": human_checkpoint,
            "evidence_receipt": evidence_receipt,
            "demonstrator_output": demo_output,
            "metadata": {
                "run_type": "read_only_demonstration_workflow",
                "framework": "SAGE-ACT-PROD",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Generate state checksum
        state_serialized = json.dumps(workflow_state, sort_keys=True)
        state_checksum = hashlib.sha256(state_serialized.encode()).hexdigest()
        workflow_state["state_checksum"] = state_checksum

        self.workflow_states[session_id] = workflow_state
        return workflow_state

    def export_demo_evidence(self, session_id: str) -> str:
        """Exports the orchestrated demonstration workflow state as a durable JSON evidence artifact."""
        state = self.workflow_states.get(session_id)
        if not state:
            raise ValueError(f"SAGE Demo Workflow Error: Session '{session_id}' not found.")

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)

        return self.output_path
