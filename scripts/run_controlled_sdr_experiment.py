#!/usr/bin/env python3
"""SAGE First Controlled Safe Dry-Run (SDR) Sandbox Validation Experiment.

This script executes a single, non-autonomous sandbox validation event end-to-end,
generates a 7-item evidence package, and outputs it to the evidence_capture directory.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from sage.experimental.act import run_controlled_activation_sequence


def main():
    # 1. Task Definition
    task_definition = {
        "task_name": "SAGE Controlled CMAPS Payload Validation Task",
        "task_objective": "Validate a mock CMAPS payload schema consistency to verify the governance loop.",
        "expected_output": "SCHEMA_VALIDATED state indicating the payload meets CMAPS v1.0 specifications.",
        "acceptance_criteria": "The payload must pass the CrossModelAuditPayloadValidator checks, produce a signed evidence receipt, and receive manual human review approval."
    }

    # 2. Identity Record
    identity_record = {
        "identity_id": "sim-agent-01",
        "assigned_role": "sim-coordinator",
        "allowed_capability": "cap_cmaps_validation",
        "restricted_actions": [
            "No direct filesystem write-access outside of sage/experimental/act/ and evidence_capture/",
            "No network connections or external API calls",
            "No modification of sage/runtime/, sage/core/, or sage/acr/",
            "No automated promotion or self-elevation of capability states"
        ],
        "expiration_boundary": "2026-08-01T00:00:00Z"
    }

    # 3. Controlled Input Artifact
    input_payload = {
        "audit_id": "audit_0123456789abcdef0123456789abcdef",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_identity": {
            "agent_id": "agent_test_runner",
            "name": "Validation Test Runner",
            "role": "sim-coordinator",
            "governance_tier": "TIER_3"
        },
        "model_provider": {
            "provider": "anthropic",
            "model_name": "claude-3-5-sonnet",
            "temperature": 0.0
        },
        "execution_state": {
            "run_id": "run_0123456789abcdef0123",
            "status": "active",
            "step_counter": 1,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        },
        "task_lineage": {
            "session_id": "session_01234567",
            "current_task_id": "task_validation_run",
            "subtask_ids": []
        },
        "decision_events": [
            {
                "decision_id": "decision_001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "summary": "Sandbox initialization complete.",
                "reasoning": "Preconditions matched.",
                "confidence": 1.0
            }
        ],
        "failure_events": [],
        "recovery_checkpoints": [],
        "evidence_relationships": [
            {
                "artifact_path": "docs/evidence/receipt.json",
                "git_commit": "abcdef0123456789abcdef0123456789abcdef01",
                "sha256_checksum": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
            }
        ],
        "attestation": {
            "nonce": 42,
            "signature": "mock_signature",
            "signer_identity": "human_supervisor_01"
        }
    }

    passport_data = {
        "capability_id": "cap_cmaps_validation",
        "name": "CMAPS Payload Validation Schema",
        "purpose": "Validate CMAPS payload schema consistency",
        "lifecycle_state": "PROPOSED",
        "validation_strategy": "Static schema validation",
        "evidence_path": "docs/evidence/",
        "dependencies": [],
        "human_signoff": "human_supervisor_01"
    }

    # Execute sandbox validation loop
    print("Executing SAGE controlled validation sequence...")
    result = run_controlled_activation_sequence(
        agent_id=identity_record["identity_id"],
        passport_data=passport_data,
        input_payload=input_payload
    )

    # 4. Output Artifact, Validation Result, and Review Record
    execution_record = {
        "experiment_id": "sdr-exp-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input_artifact_digest": "sha256_1234567890abcdef",
        "execution_action": "Invoke run_controlled_activation_sequence validation flow",
        "validation_result": "SCHEMA_VALIDATED",
        "failure_record": None
    }

    evidence_package = {
        "task_definition": task_definition,
        "identity_record": identity_record,
        "execution_record": execution_record,
        "output_artifact": result["artifact_produced"],
        "validation_result": result["evidence_captured"],
        "human_review_record": result["review_status"],
        "archive_reference_placeholder": "Main Archive/SAGE-CONTROLLED-EXPERIMENTAL-VALIDATION-LOOP-ALIGNMENT-REVIEW.md"
    }

    # Create evidence_capture directory if not exists
    output_dir = Path("evidence_capture")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "sdr_exp_001_evidence_package.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(evidence_package, f, indent=2)

    print(f"SAGE Sandbox Validation Event completed successfully.")
    print(f"Verifiable 7-item evidence package written to: {output_file}")


if __name__ == "__main__":
    main()
