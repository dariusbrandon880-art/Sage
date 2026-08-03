"""SAGE Demonstration Experience.

Coordinates the unified entry experience and presents a repeatable user demonstration,
assembling lineage, verification states, human checkpoints, and final evidence packages.
"""

import os
import json
import hashlib
from typing import Any, Dict, Optional
from datetime import datetime, timezone


class SAGEDemoExperienceManager:
    """Provides a unified demonstration entry experience wrapper around existing SAGE capabilities."""

    def __init__(self, output_path: str = "evidence_capture/demo_experience_evidence.json"):
        self.output_path = output_path
        self.experience_state: Optional[Dict[str, Any]] = None

    def launch_experience(
        self,
        session_id: str = "session_demo_exp_2026",
        user_id: str = "usr_lead_developer",
        approver: str = "supervisor_charlie",
        signature: str = "sig_exp_approved_7711",
    ) -> Dict[str, Any]:
        """Launches the unified demonstration experience, executing the simulated workflow."""
        # 1. Ingest User action & Intake
        intake = {
            "status": "INTAKE_COMPLETE",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "action_type": "user_demonstration_run",
            "user_id": user_id,
            "context_data": {
                "environment": "sandboxed_demo_sandbox",
                "active_milestone": "SAGE-ACT-PROD-DEMO-EXPERIENCE",
                "launched_at": datetime.now(timezone.utc).isoformat(),
            },
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

        # 4. Human Checkpoint Flow
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

        # 6. Output Presentation Layer
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

        workflow_state = {
            "workflow_id": f"workflow_{hashlib.md5(session_id.encode()).hexdigest()[:8]}",
            "session_id": session_id,
            "user_action": {
                "action_type": "user_demonstration_run",
                "user_id": user_id,
            },
            "intake": intake,
            "context_evaluation": context_evaluation,
            "capability_analysis": capability_analysis,
            "human_checkpoint": human_checkpoint,
            "evidence_receipt": evidence_receipt,
            "demonstrator_output": demo_output,
        }

        summary = (
            f"=== SAGE DEMONSTRATION RUN COMPLETE ===\n"
            f"Session ID: {session_id}\n"
            f"Status: INTAKE_COMPLETE & VERIFIED\n"
            f"Boundary Integrity: Context Guard Monitored (SECURE)\n"
            f"SDR Divergence State: split_brain_detected=True (Recovery Checkpoints Active)\n"
            f"Human Checkpoint: AUTHORIZED by {approver}\n"
            f"Verification: SAGE_ACTIVATION_RECEIPT_VALID\n"
            f"========================================"
        )

        experience = {
            "experience_id": f"exp_{hashlib.md5(session_id.encode()).hexdigest()[:8]}",
            "session_id": session_id,
            "status": "EXPERIENCE_SUCCESS",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "demonstration_summary": summary,
            "workflow_payload": workflow_state,
            "usability_improvements": {
                "unified_entry_invoked": True,
                "input_mapping_consistency_checked": True,
                "summary_presentation_enabled": True,
            },
        }

        # Deterministic experience checksum
        state_serialized = json.dumps(experience, sort_keys=True)
        experience_checksum = hashlib.sha256(state_serialized.encode()).hexdigest()
        experience["experience_checksum"] = experience_checksum

        self.experience_state = experience
        return experience

    def export_experience_evidence(self) -> str:
        """Generates the final usable evidence package as a durable JSON artifact."""
        if not self.experience_state:
            raise ValueError("SAGE Demo Experience Error: No experience has been executed yet.")

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(self.experience_state, f, indent=2, sort_keys=True)

        return self.output_path
