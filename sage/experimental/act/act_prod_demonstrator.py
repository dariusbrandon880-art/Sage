"""SAGE-ACT-PROD Demonstrator Foundation.

Provides a read-only sandboxed visualizer and data compiler for SAGE lineage,
divergence, recovery, and receipt verification tracking.
"""

import os
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class SAGEProdDemonstrator:
    """Read-only demonstrator representing state and lineages from active SAGE capabilities."""

    def __init__(self, output_path: str = "evidence_capture/act_prod_demonstrator_run.json"):
        self.output_path = output_path
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def load_simulated_inputs(self) -> Dict[str, Any]:
        """Loads default/simulated inputs from prior validated capabilities."""
        return {
            "activation_layer": {
                "session_id": "session_act_9081",
                "action_type": "code_evaluation",
                "status": "intake_complete",
                "receipt_id": "receipt_7a2b9f3c1a",
                "verification_hash": "a4f89d82b0f49c0d127393fe37ae883c4b9d0e12f38ab90cd1235fe99bc0e712",
            },
            "context_guard": {
                "guard_status": "SECURE",
                "protected_paths_detected": ["sage/runtime/", "sage/core/"],
                "violations_prevented": 3,
                "interactive_approval_simulation": "GRANTED",
            },
            "sdr_004": {
                "divergence_detected": True,
                "conflict_type": "state_split_brain",
                "divergent_agents": ["agent_research", "agent_reviewer"],
                "loops_detected": 0,
                "recovery_checkpoints": [
                    {
                        "checkpoint_id": "chk_rec_001_initial",
                        "status": "restored",
                        "authority_restored": "supervisor_lead",
                        "timestamp": "2026-03-31T12:05:00Z",
                    }
                ],
            },
            "crc_002": {
                "asymmetric_signed": True,
                "signer_identity": "sage_acr_signer",
                "receipt_chain_length": 4,
                "signature_valid": True,
                "attestation": "SAGE_TRUST_ATTESTATION_SUCCESS",
            },
        }

    def compile_demonstration_state(
        self,
        session_id: str,
        user_id: str,
        approver: str,
        signature: str,
    ) -> Dict[str, Any]:
        """Compiles the integrated state lineage, divergence tracking, and checkpoint status."""
        inputs = self.load_simulated_inputs()

        # Build demonstrator state
        state = {
            "session_id": session_id,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs_mapped": list(inputs.keys()),
            "demonstrator_metadata": {
                "version": "1.0.0-demonstrator",
                "mode": "read_only_experimental_sandbox",
            },
            "lineage_visualization": {
                "active_session": inputs["activation_layer"]["session_id"],
                "session_status": inputs["activation_layer"]["status"],
                "guard_status": inputs["context_guard"]["guard_status"],
                "protected_paths": inputs["context_guard"]["protected_paths_detected"],
            },
            "divergence_visibility": {
                "divergence_detected": inputs["sdr_004"]["divergence_detected"],
                "conflict_type": inputs["sdr_004"]["conflict_type"],
                "divergent_agents": inputs["sdr_004"]["divergent_agents"],
            },
            "recovery_checkpoint_visibility": {
                "checkpoints": inputs["sdr_004"]["recovery_checkpoints"],
            },
            "receipt_verification_display": {
                "receipt_id": inputs["activation_layer"]["receipt_id"],
                "verification_hash": inputs["activation_layer"]["verification_hash"],
                "asymmetric_signed": inputs["crc_002"]["asymmetric_signed"],
                "signature_valid": inputs["crc_002"]["signature_valid"],
                "attestation": inputs["crc_002"]["attestation"],
            },
            "human_review_checkpoint_simulation": {
                "checkpoint_triggered": True,
                "approver": approver,
                "signature": signature,
                "status": "AUTHORIZED",
                "authorized_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Compute deterministic checksum of the state payload
        serialized = json.dumps(state, sort_keys=True)
        checksum = hashlib.sha256(serialized.encode()).hexdigest()
        state["demonstrator_checksum"] = checksum

        self.sessions[session_id] = state
        return state

    def export_evidence_artifact(self, session_id: str) -> str:
        """Exports compiled demonstrator state as a durable JSON evidence artifact."""
        state = self.sessions.get(session_id)
        if not state:
            raise ValueError(f"SAGE Demonstrator Error: Session '{session_id}' not found.")

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)

        return self.output_path


def render_html_visualizer(state_data: Dict[str, Any]) -> str:
    """Generates visual elements using the HTML template, embedding compiled SAGE metrics."""
    template_path = "sage/experimental/act/templates/act_prod_visualizer.html"
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Visualizer HTML template not found at {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Simple template substitution
    rendered = template.replace(
        "{{SAGE_STATE_JSON}}", json.dumps(state_data, indent=2)
    ).replace(
        "{{SESSION_ID}}", state_data.get("session_id", "N/A")
    ).replace(
        "{{DEMONSTRATOR_CHECKSUM}}", state_data.get("demonstrator_checksum", "N/A")
    ).replace(
        "{{HUMAN_APPROVER}}", state_data.get("human_review_checkpoint_simulation", {}).get("approver", "N/A")
    )

    return rendered
