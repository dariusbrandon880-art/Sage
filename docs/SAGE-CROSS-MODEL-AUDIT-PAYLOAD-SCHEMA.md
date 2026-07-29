# SAGE Cross-Model Audit Payload Schema

**Document Identifier:** SAGE-ACT-CMAPS-1.0
**Classification:** Experimental Schema Specification
**Status:** PROPOSED
**Author:** Jules (SAGE Engineering Node)
**Date:** March 2026

---

## 1. Schema Purpose

In a heterogeneous, multi-agent cognitive architecture, agents are dispatched across various Large Language Models (LLMs) and API providers (e.g., OpenAI GPT series, Anthropic Claude, Google Gemini, and local fine-tuned models). Each provider and model introduces unique outputs, response structures, latencies, and error patterns.

To maintain cognitive continuity, security, and architectural alignment, SAGE requires a **model-independent execution and audit tracking standard**.

The **SAGE Cross-Model Audit Payload Schema (CMAPS)** defines a unified, machine-validatable evidence structure that captures the full operational lifecycle of any SAGE agent, regardless of the underlying model or hosting provider. By standardizing this payload, SAGE can:
1. **Ensure Platform Portability:** Rehydrate agent states seamlessly when migrating tasks between models (e.g., fallback from a cloud API to an offline model).
2. **Enforce Deterministic Auditing:** Provide cryptographic-grade proof of execution lineages, decisions, and attestation nonces.
3. **Facilitate Failure Recovery:** Intercept, classify, and recover from failures using standardized checkpoint snapshots.

---

## 2. Field Definitions

An audit payload conforming to CMAPS v1.0 must contain the following top-level structures:

```
{
  "$schema": "https://sage.cos.core/schemas/audit-payload-v1.json",
  "audit_id": "audit_...",
  "timestamp": "ISO-8601 UTC",
  "agent_identity": { ... },
  "model_provider": { ... },
  "execution_state": { ... },
  "task_lineage": { ... },
  "decision_events": [ ... ],
  "failure_events": [ ... ],
  "recovery_checkpoints": [ ... ],
  "evidence_relationships": [ ... ],
  "attestation": { ... }
}
```

### 2.1. Top-Level Elements
* **`$schema`** (string, required): URI of the schema definition.
* **`audit_id`** (string, required): Unique identifier for this audit record, prefixed with `audit_` followed by a UUIDv4 or hex string.
* **`timestamp`** (string, required): ISO-8601 UTC timestamp of payload generation.

### 2.2. Agent Identity (`agent_identity`)
Uniquely identifies the agent instance performing the execution.
* **`agent_id`** (string, required): Identifier of the agent, prefixed with `agent_`.
* **`name`** (string, required): Descriptive name of the agent.
* **`role`** (string, required): The role or system tier of the agent (e.g., `orchestrator`, `planner`, `coder`, `auditor`).
* **`governance_tier`** (string, required): Governance level (e.g., `canonical`, `experimental`, `shadow`).

### 2.3. Model & Provider Identity (`model_provider`)
Captures the execution environment's LLM parameters.
* **`provider`** (string, required): The service hosting the model (e.g., `openai`, `anthropic`, `google`, `ollama`).
* **`model_name`** (string, required): The exact model designation (e.g., `gpt-4o`, `claude-3-5-sonnet-v2`, `gemini-1.5-pro`).
* **`temperature`** (number, required): Temperature setting (between `0.0` and `2.0`).
* **`max_tokens`** (integer, optional): Maximum tokens limit requested.
* **`api_version`** (string, optional): API version tag.

### 2.4. Execution State (`execution_state`)
Describes the current lifecycle phase and telemetry.
* **`run_id`** (string, required): Identifier of the execution run, prefixed with `run_`.
* **`status`** (string, required): Current execution status. Allowed values: `active`, `suspended`, `completed`, `failed`, `recovered`.
* **`step_counter`** (integer, required): Monotonically increasing counter of steps executed.
* **`started_at`** (string, required): ISO-8601 timestamp of when the run was initiated.
* **`updated_at`** (string, required): ISO-8601 timestamp of the last state update.

### 2.5. Task Lineage (`task_lineage`)
Maps the relationship tree of the active cognitive task.
* **`session_id`** (string, required): High-level cognitive session ID, prefixed with `session_`.
* **`parent_task_id`** (string, optional): ID of the task that spawned this task, prefixed with `task_`.
* **`current_task_id`** (string, required): Active task ID, prefixed with `task_`.
* **`subtask_ids`** (array of strings, required): List of child task IDs spawned during this run.

### 2.6. Decision Events (`decision_events`)
A chronological log of all governance, architectural, or logic-level decisions made during the execution block.
* **`decision_id`** (string, required): Unique identifier, prefixed with `decision_` or `proposal_`.
* **`timestamp`** (string, required): ISO-8601 timestamp of when the decision occurred.
* **`summary`** (string, required): Succinct description of the decision.
* **`reasoning`** (string, required): The rationale or cognitive chain-of-thought leading to this decision.
* **`confidence`** (number, required): Confidence level of the choice, from `0.0` to `1.0`.

### 2.7. Failure Events (`failure_events`)
Log of intercepted exceptions, boundaries broken, or execution failures.
* **`failure_id`** (string, required): Unique identifier, prefixed with `fail_`.
* **`timestamp`** (string, required): ISO-8601 timestamp of when the failure occurred.
* **`error_type`** (string, required): Class name of the exception or error type (e.g., `AgentBoundaryInterceptionError`).
* **`message`** (string, required): Detailed error message.
* **`severity`** (string, required): Severity level. Allowed values: `low`, `medium`, `high`, `critical`.
* **`stack_trace`** (string, optional): Intercepted code-level stack trace.

### 2.8. Recovery Checkpoints (`recovery_checkpoints`)
State snapshots and rollback configurations designed to facilitate graceful recovery or human-in-the-loop rehydration.
* **`checkpoint_id`** (string, required): Unique identifier, prefixed with `chk_`.
* **`timestamp`** (string, required): ISO-8601 timestamp of the snapshot.
* **`rehydration_token`** (string, required): Unique secure key or hash used to rehydrate this state.
* **`rollback_state_ref`** (string, optional): Reference to a previous clean state to revert to if recovery fails.
* **`requires_human_approval`** (boolean, required): Flag indicating if human intervention is mandatory before proceeding.

### 2.9. Evidence Relationships (`evidence_relationships`)
Ensures cryptographic traceabilty and links the execution payload to real-world artifacts.
* **`artifact_path`** (string, required): Path of the file or database collection associated with this execution.
* **`git_commit`** (string, required): Git SHA-1 commit hash representing the exact code state under which this execution took place.
* **`sha256_checksum`** (string, required): SHA-256 hash of the generated or reviewed files.

### 2.10. Attestation (`attestation`)
Cryptographic signature and nonce block to prevent tampering, forgery, or replay attacks.
* **`nonce`** (string, required): Single-use cryptographically random string.
* **`signature`** (string, required): Hex-encoded cryptographic signature (e.g., HMAC-SHA256) of the entire JSON payload excluding the signature field itself.
* **`signer_identity`** (string, required): Public key or identifier of the validating authority.

---

## 3. Example Payload

Below is a complete, compliant instance of a SAGE Cross-Model Audit Payload representing an agent executing a deployment task on Claude-3-5-Sonnet, suffering an intercepted boundary error, and successfully checkpointing its state:

```json
{
  "$schema": "https://sage.cos.core/schemas/audit-payload-v1.json",
  "audit_id": "audit_8f9c0e1b2a3d4e5f6a7b8c9d0e1f2a3b",
  "timestamp": "2026-03-30T14:45:30.123456Z",
  "agent_identity": {
    "agent_id": "agent_reliability_monitor_v1",
    "name": "SAGE Reliability Guard",
    "role": "auditor",
    "governance_tier": "experimental"
  },
  "model_provider": {
    "provider": "anthropic",
    "model_name": "claude-3-5-sonnet-v2",
    "temperature": 0.2,
    "max_tokens": 4096,
    "api_version": "2023-06-01"
  },
  "execution_state": {
    "run_id": "run_01j7p8f9q0a1b2c3d4e5f6g7h8",
    "status": "failed",
    "step_counter": 14,
    "started_at": "2026-03-30T14:30:00.000000Z",
    "updated_at": "2026-03-30T14:45:30.123456Z"
  },
  "task_lineage": {
    "session_id": "session_f6b3d4e5",
    "parent_task_id": "task_root_deploy_001",
    "current_task_id": "task_sub_verify_002",
    "subtask_ids": []
  },
  "decision_events": [
    {
      "decision_id": "decision_001_approve_credentials",
      "timestamp": "2026-03-30T14:35:10.000000Z",
      "summary": "Verified API credentials for external workspace integration.",
      "reasoning": "Inspected credentials matches the SHA256 fingerprints registered in the Secure Vault, satisfying SPEK v1.1 rules.",
      "confidence": 0.98
    }
  ],
  "failure_events": [
    {
      "failure_id": "fail_001_boundary_leak",
      "timestamp": "2026-03-30T14:45:28.987654Z",
      "error_type": "AgentBoundaryInterceptionError",
      "message": "Attempted to write to a protected production namespace '/app/sage/core/spek.py' inside an experimental session.",
      "severity": "critical",
      "stack_trace": "Traceback (most recent call last):\n  File \"/app/sage/experimental/act/agent_runner.py\", line 42, in run_step\n    self.boundary_manager.verify_write_path(target_path)\n  AgentBoundaryInterceptionError: Attempted to write to a protected production namespace '/app/sage/core/spek.py' inside an experimental session."
    }
  ],
  "recovery_checkpoints": [
    {
      "checkpoint_id": "chk_001_recovery_snapshot",
      "timestamp": "2026-03-30T14:45:30.000000Z",
      "rehydration_token": "rehyd_01j7p8g9r0b1c2d3e4f5g6h7i8",
      "rollback_state_ref": "chk_000_initial_clean_state",
      "requires_human_approval": true
    }
  ],
  "evidence_relationships": [
    {
      "artifact_path": "sage/experimental/act/contracts.py",
      "git_commit": "7553d9b0fb40234008875b534a97ceb653111f82",
      "sha256_checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    }
  ],
  "attestation": {
    "nonce": "a7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2",
    "signature": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9",
    "signer_identity": "sage_validator_pubkey_01"
  }
}
```

---

## 4. Lineage Mapping

Cognitive continuity requires that every low-level model operation is causally bound to high-level, human-approved objectives. CMAPS maps this structural relationship explicitly via identifiers in the `task_lineage` block:

```
  Session State              Agent Tasks                Causal Decisions
┌──────────────┐         ┌───────────────────┐         ┌─────────────────┐
│              │         │ parent_task_id    │         │                 │
│  session_id  │ ──────> │   (task_root_...) │ ──────> │   decision_id   │
│              │         │                   │         │                 │
└──────────────┘         │ current_task_id   │         └─────────────────┘
                         │   (task_sub_...)  │
                         └───────────────────┘
```

1. **Session Anchor:** The `session_id` connects the payload to a state object managed by `SessionStateManager` in `sage/acr/session/session_state.py`.
2. **Task Inheritance:** The hierarchical link between `parent_task_id` and `current_task_id` allows SAGE to construct a directed acyclic graph (DAG) representing multi-agent delegation pipelines.
3. **Causal Binding:** All entries in `decision_events` must refer to the `current_task_id`, allowing researchers to reconstruct the precise sequence of thoughts and actions that culminated in an architectural or process decision.

---

## 5. Failure & Recovery Mapping

The SAGE Agent Reliability Layer foundation specifies a dual-loop resilience process: the **Graceful Intercept Loop** and the **State Rehydration Loop**. CMAPS represents this process explicitly.

### 5.1. Graceful Intercept Loop
When an agent encounters a system error or boundary violation:
1. The execution engine intercepts the exception and constructs a `failure_events` block.
2. The `execution_state.status` transitions to `failed` or `suspended`.
3. The engine captures a frozen, non-mutable state of the active environment, assigning a `checkpoint_id`.

### 5.2. State Rehydration Loop
To recover or rehydrate the agent state:
1. SAGE retrieves the `recovery_checkpoints` block associated with the last successful run.
2. If `requires_human_approval` is `true`, SAGE halts execution and registers a rehydration prompt in the Human-SAGE Interaction (HSI) queue.
3. Once approved, the `rehydration_token` is exchanged for the state payload stored in the persistence vault, allowing the agent to resume execution from the exact step counter where the failure was recorded.

---

## 6. Validation Requirements

A Cross-Model Audit Payload is only promoted to the Master Archive if it satisfies the following programmatic constraints:

### 6.1. Structural Format and Pattern Integrity
All identifiers in the payload must strictly match predefined regular expressions to prevent format injections or un-indexed orphans:
* `audit_id`: `^audit_[a-fA-F0-9]{32}$`
* `agent_identity.agent_id`: `^agent_[a-zA-Z0-9_]{3,64}$`
* `execution_state.run_id`: `^run_[a-zA-Z0-9]{20,40}$`
* `task_lineage.session_id`: `^session_[a-fA-F0-9]{8}$`
* `task_lineage.current_task_id`: `^task_[a-zA-Z0-9_]{3,128}$`
* `task_lineage.parent_task_id`: `^task_[a-zA-Z0-9_]{3,128}$` (if present)
* `decision_events[].decision_id`: `^(decision|proposal)_[a-zA-Z0-9_]{3,128}$`
* `failure_events[].failure_id`: `^fail_[a-zA-Z0-9_]{3,128}$`
* `recovery_checkpoints[].checkpoint_id`: `^chk_[a-zA-Z0-9_]{3,128}$`

### 6.2. Chronological Invariants
* **Run Timeline Consistency:** `started_at` must be chronologically earlier than or equal to `updated_at`.
* **Decision Causality:** Every timestamp inside `decision_events` must be chronologically later than or equal to `started_at` of the active run.
* **Failure Interception Order:** The `failure_events[].timestamp` must be chronologically earlier than or equal to `recovery_checkpoints[].timestamp`.

### 6.3. Relational and Multi-Set Uniqueness
* **No Task Duplication:** `current_task_id` must not be present in `subtask_ids`.
* **Unique Decision Identifiers:** All `decision_id` values within the payload must be mutually unique.
* **Unique Checkpoint Tokens:** All `rehydration_token` values must be unique and never reused across runs (nonce-like behavior).

### 6.4. Cryptographic Proof Verification
* **Nonce Integrity:** The `attestation.nonce` must not exist in SAGE's `NonceLedger` (`sage/acr/nonce_ledger.py`), indicating that the payload is fresh and not a replayed message.
* **HMAC/Signature Match:** The validation system re-computes the HMAC-SHA256 signature of the payload using the validating authority's registered public key and compares it against `attestation.signature`. Any mismatch immediately triggers a `VALIDATION_FAIL` and rejects archive promotion.

---

## 7. Future Extension Points

SAGE CMAPS is designed with modular expansion in mind to support future capability upgrades:

1. **Multi-Modal Audit Captures:** Extending `evidence_relationships` to capture model-generated canvas layouts, audio tokens, or visual frame screenshots for spatial agents.
2. **Federated Governance Consensus:** Allowing multiple consensus signers in the `attestation` block, requiring a M-of-N signature quorum before a payload is promoted to `CANONICAL` status.
3. **Acyclic Path-Pruning Engines:** Optimizing memory consumption by automatically pruning redundant checkpoints on completed sessions, preserving only the causal boundary checkpoints.

---

## 8. SAGE Strategic Architecture Research Input Appendix

This appendix catalogues long-term, non-active research tracks evaluated under SAGE's governance loop. These tracks represent future theoretical directions to explore under strict experimental isolation, with zero implementation footprint on SAGE core or production runtimes.

### 8.1. Track A — SAGE State Representation Layer (SSRL)
* **Research Question:** Can SAGE represent durable operational state independent of any single LLM or model architecture?
* **Research Constraints:**
  - Do not capture hidden model states.
  - Do not depend on proprietary latent representations.
  - Focus exclusively on operational state: objectives, dependencies, constraints, evidence, execution history, and recovery context.
* **Lineage Mapping:** Extends SAGE's focus on model-independent tracing, laying the foundation for cross-provider transaction logs.

### 8.2. Track B — SAGE Recovery Architecture (SRA)
* **Research Question:** How can autonomous workflows fail safely through recoverable checkpoints?
* **Focus Areas:** Failure state capture, recovery records, execution checkpoints, and evidence preservation.
* **Lineage Mapping:** Conceptualizes multi-hop rollback mechanisms building upon the CMAPS v1.0 recovery schema definitions.

### 8.3. Track C — CMAPS Evolution Contract (CEC)
* **Research Question:** How can CMAPS evolve from an evidence payload schema into a formal state transition contract?
* **Focus Areas:** Preconditions, validated transitions, evidence relationships, and archive promotion rules.
* **Status:** CMAPS remains categorized strictly as a **Validated Experimental Specification**. No promotion beyond this current lifecycle state is authorized.

### 8.4. Track D — Cognitive Infrastructure Boundary (CIB)
* **Research Question:** What minimum boundary preserves SAGE identity independent from external model providers?
* **Focus Areas:** Core ownership boundaries, model-provider independence, and continuity preservation.

### 8.5. Archived Long-Term Concepts
The following trajectories are archived as future research only to prevent premature complexity:
* **Distributed Ledger Architecture:** Deemed premature complexity; focus remains on central, cryptographic validation receipts.
* **Cognitive HAL Architecture:** Deferred; focus remains on standard provider wrappers.
* **Universal Cryptographic Proof Systems:** Deferred; focus remains on HMAC-SHA256 attestation primitives.
