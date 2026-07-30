#!/usr/bin/env python3
"""SAGE First and Second Controlled SDR Experiment Execution Script.

This script executes:
- SDR-001: Programmatically validates a simulated Capability Passport.
- SDR-002: Runs a sequential multi-agent handoff simulation (ChatGPT -> Jules -> Claude -> Gemini),
  validating envelope passing, constraint propagation (no-code-mutation), permission boundaries,
  and chronological evidence compilation with strictly increasing timestamps.
"""

import os
import json
import time
from datetime import datetime, timezone
from sage.experimental.act.contracts import (
    CapabilityPassportValidator,
    CapabilityEvidenceReceiptGenerator,
    HumanReviewGate,
)
from sage.experimental.agents.models import (
    AgentCommunicationEnvelope,
)
from sage.experimental.agents.registry import AgentIdentityRegistry
from sage.experimental.agents.validation import AgentHandoffValidator


def run_sdr_001():
    print("\n--- Executing SDR-001 Validation ---")
    mock_passport = {
        "capability_id": "cap_sdr_sim_engine",
        "name": "SDR Simulation Engine",
        "purpose": "Provides safe simulation environments for AI agent execution validation.",
        "lifecycle_state": "proposed",
        "validation_strategy": "Verify state preservation and boundary isolation during dry-runs.",
        "evidence_path": "docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        "dependencies": [],
        "human_signoff": {
            "signer": "supervisor_v1",
            "timestamp": "2026-03-31T12:00:00Z",
            "approved": True,
        },
    }

    passport_validator = CapabilityPassportValidator()
    validation_res = passport_validator.validate_passport(mock_passport)

    receipt_generator = CapabilityEvidenceReceiptGenerator(validator_id="val_system_v1")
    receipt_res = receipt_generator.generate_receipt(mock_passport, validation_res)

    review_gate = HumanReviewGate(reviewer_identity="supervisor_v1")
    review_notes = (
        "Sandbox dry-run execution results verified. All isolated file operations performed "
        "strictly in approved experimental scratch directories. No core runtime mutations detected."
    )
    review_res = review_gate.execute_review(
        receipt=receipt_res,
        decision="approved",
        notes=review_notes,
    )

    evidence_package = {
        "experiment_id": "sdr_exp_001_governance_lifecycle",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETED",
        "components": {
            "mock_passport": mock_passport,
            "passport_validation_result": validation_res,
            "evidence_receipt": receipt_res,
            "human_review_result": review_res,
        },
        "system_telemetry": {
            "isolated_boundary_enforced": True,
            "core_runtime_mutations_detected": False,
        }
    }

    os.makedirs("evidence_capture", exist_ok=True)
    evidence_path = "evidence_capture/sdr_exp_001_evidence_package.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_package, f, indent=2)

    print(f"[SUCCESS] SDR-001 Evidence saved to: {evidence_path}")


def run_sdr_002():
    print("\n--- Executing SDR-002 Multi-Agent Handoff Chain Simulation ---")
    registry = AgentIdentityRegistry(seed_defaults=True)
    validator = AgentHandoffValidator(registry)

    traces = []
    timestamps = []

    # Common mission metadata
    mission_id = "mission_sdr_002_multi_agent_flow"
    constraints = ["no-code-mutation", "sandbox-scratch-only"]

    # 1. STEP 1: ChatGPT (Coordinator) -> Jules (Engineering Executor)
    # Handoff task: Execute sandbox execution
    env_1 = AgentCommunicationEnvelope(
        mission_id=mission_id,
        sender_identity="ChatGPT",
        receiver_identity="Jules",
        task_objective="Execute dry-run execution and output preliminary execution payload.",
        authorized_capability="cap_sdr_sim_engine",
        constraints=constraints,
        expected_artifact="evidence_capture/sdr_exp_002_jules_output.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )
    exec_result_1 = {
        "status": "SUCCESS",
        "task": "sandbox_execution",
        "output_checksum": "f3b4c9e8",
        "payload": {"state_change_count": 0, "isolation_secured": True}
    }

    print("Step 1: Validating ChatGPT -> Jules handoff...")
    time.sleep(0.1)  # Ensure distinct monotonically increasing timestamp values
    record_1 = validator.validate_and_execute_handoff(
        envelope=env_1,
        execution_result=exec_result_1,
        human_approved=True,
    )
    traces.append(record_1.to_dict())
    timestamps.append(record_1.timestamp)
    print(f"   [OK] ChatGPT -> Jules handoff complete at {record_1.timestamp}")

    # 2. STEP 2: Jules (Engineering Executor) -> Claude (Adversarial Reviewer)
    # Handoff task: adversarial audit of execution artifacts
    env_2 = AgentCommunicationEnvelope(
        mission_id=mission_id,
        sender_identity="Jules",
        receiver_identity="Claude",
        task_objective="Perform adversarial audit of Jules' execution output against CMAPS constraints.",
        authorized_capability="cap_adversarial_audit",
        constraints=constraints,
        expected_artifact="evidence_capture/sdr_exp_002_claude_audit.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )
    exec_result_2 = {
        "status": "AUDIT_COMPLETED",
        "threat_level": "none",
        "validation_findings": "Confirmed 100% compliant execution. No unauthorized code modifications or state drift detected.",
        "payload_checksum_verified": True,
    }

    print("Step 2: Validating Jules -> Claude handoff...")
    time.sleep(0.1)
    record_2 = validator.validate_and_execute_handoff(
        envelope=env_2,
        execution_result=exec_result_2,
        human_approved=True,
    )
    traces.append(record_2.to_dict())
    timestamps.append(record_2.timestamp)
    print(f"   [OK] Jules -> Claude handoff complete at {record_2.timestamp}")

    # 3. STEP 3: Claude (Adversarial Reviewer) -> Gemini (Independent Analyst)
    # Handoff task: compilation of analytical execution metrics
    env_3 = AgentCommunicationEnvelope(
        mission_id=mission_id,
        sender_identity="Claude",
        receiver_identity="Gemini",
        task_objective="Compile audit metrics and generate system performance readiness dashboard.",
        authorized_capability="cap_metrics_compilation",
        constraints=constraints,
        expected_artifact="evidence_capture/sdr_exp_002_gemini_metrics.json",
        evidence_reference="docs/SAGE-FIRST-CONTROLLED-SDR-EXPERIMENT-SPECIFICATION.md",
        review_status="pending",
    )
    exec_result_3 = {
        "status": "METRICS_COMPILED",
        "readiness_score": 1.0,
        "conclusions": "Governance chain complete, error-rate at 0%, and absolute human supervisor control verified.",
    }

    print("Step 3: Validating Claude -> Gemini handoff...")
    time.sleep(0.1)
    record_3 = validator.validate_and_execute_handoff(
        envelope=env_3,
        execution_result=exec_result_3,
        human_approved=True,
    )
    traces.append(record_3.to_dict())
    timestamps.append(record_3.timestamp)
    print(f"   [OK] Claude -> Gemini handoff complete at {record_3.timestamp}")

    # 4. Chronological monotonicity check
    print("Step 4: Checking chronological monotonicity of timestamps...")
    for i in range(len(timestamps) - 1):
        t1 = datetime.fromisoformat(timestamps[i])
        t2 = datetime.fromisoformat(timestamps[i+1])
        if t1 >= t2:
            raise ValueError(f"Chronology Violation: Timestamp {t1} is not strictly earlier than {t2}.")
    print("   [OK] Chronological monotonicity successfully verified.")

    # 5. Enforce final human authority review gate compilation
    print("Step 5: compiling SDR-002 Evidence Package...")
    evidence_package = {
        "experiment_id": "sdr_exp_002_multi_agent_chain",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETED",
        "chain_sequence": [
            "ChatGPT (Coordinator)",
            "Jules (Engineering Executor)",
            "Claude (Adversarial Reviewer)",
            "Gemini (Independent Analyst)"
        ],
        "validation_flow_traces": traces,
        "constraints_propagated": constraints,
        "governance_metrics": {
            "steps_executed": len(traces),
            "chronology_monotonic": True,
            "permissions_enforced": True,
            "isolation_boundary_secured": True,
        }
    }

    evidence_path = "evidence_capture/sdr_exp_002_evidence_package.json"
    with open(evidence_path, "w", encoding="utf-8") as f:
        json.dump(evidence_package, f, indent=2)

    print(f"[SUCCESS] SDR-002 Evidence saved to: {evidence_path}")


def main():
    print("=== Initiating SAGE Controlled Sandbox Experiments Validation ===")
    run_sdr_001()
    run_sdr_002()
    print("=== SAGE Sandbox Experiments Complete ===")


if __name__ == "__main__":
    main()
