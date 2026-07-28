# SAGE Agent Reliability Layer v1: Controlled Rehydration Research Specification

**Document Identifier:** SAGE-ARL-RRS-1.0
**Classification:** Experimental Specification Document
**Status:** PROPOSED
**Author:** Jules (SAGE Engineering Node)
**Date:** March 2026

---

## 1. Executive Summary

This specification outlines the technical design, parsing pipelines, and rehydration protocols for the **SAGE Agent Reliability Layer v1 Controlled Rehydration** phase.

Controlled Rehydration represents the logical progression from **Graceful Intercept** (which captures boundary infractions and outputs serialised checkpoints) to **Workflow Recovery** (which reads a validated checkpoint, recovers execution context, and resumes simulated agent execution safely).

All research patterns, structures, and mock implementations remain strictly restricted within the experimental boundary namespace (`sage/experimental/act/`) and conform to SAGE's zero-touch baseline protection guarantees.

---

## 2. Rehydration Pipeline Architecture

The Controlled Rehydration workflow is structured as a three-stage pipeline: **Parse & Verify**, **Context Rehydration**, and **Safe Completion**.

```
    [Audit Payload JSON] (docs/SAGE-AGENT-RELIABILITY-AUDIT-PAYLOAD-SCHEMA-V1.md)
             │
             ▼
    ┌─────────────────────────────────┐
    │ 1. Parse & Verify Stage         │
    │    - JSON Validation            │
    │    - Check Human Approval Sign  │
    └─────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │ 2. Context Rehydration Stage    │
    │    - Fetch Snapshot (State)     │
    │    - Re-instantiate Worker      │
    └─────────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────┐
    │ 3. Safe Completion Stage        │
    │    - Resume Workflow On-Memory  │
    │    - Lineage Validation         │
    └─────────────────────────────────┘
```

### 2.1. Stage 1: Parse and Verify
The rehydration engine parses the JSON-compatible `SageAgentReliabilityAuditPayload` structure. It enforces the following validation checks prior to context rehydration:
- **Payload Struct Conformity**: Checks that all schema blocks (`identity`, `state`, `failure_event`, `decision_lineage`, `recovery`) are fully present.
- **Human Approval Verification**: Inspects `recovery.human_approval_required`. If true, the system asserts that a valid cryptographic signature is present in the rehydration transaction metadata.

### 2.2. Stage 2: Context Rehydration
Upon verification, the engine retrieves the state snapshot referenced in `state.active_state_snapshot_ref`. This retrieves:
- The last successfully completed steps (`state.previous_steps`).
- The in-memory variables and context of the failing workflow step.
- The original session variables mapped via `SessionStateTaskLinker`.

The engine then instantiates a new `GovernedAgentSimWorker` with updated, widened `PermissionBoundary` limits (or alternative paths) that successfully resolve the original boundary conflict.

### 2.3. Stage 3: Safe Completion
The newly rehydrated sim worker resumes the remaining task steps strictly on-memory:
- It processes the step that originally triggered the graceful intercept.
- It records new, successful `TaskEvent` traces.
- The final lineage trees are submitted to `SessionStateTaskLinker` and `TaskDecisionCausalBinder` to ensure chronological and objective alignments remain intact, closing the evidence loop.

---

## 3. Proposed Class and Interface Design

We propose the following read-only, non-mutating interface structure inside `sage/experimental/act/agent_runner.py` for future implementation:

```python
class GovernedAgentRehydrator:
    """Manages parsing, human signature verification, and on-memory rehydration of failed agent states."""

    def __init__(self, validation_mode: str = "strict"):
        self.validation_mode = validation_mode

    def verify_human_approval(self, payload: Dict[str, Any], approval_signature: str) -> bool:
        """Verifies that the recovery checkpoint is signed by an authorized human authority.

        Returns:
            True if the signature is valid, False otherwise.
        """
        # Under experimental rules, checks standard mock signatures (e.g., 'human_jules_sig_123')
        checkpoint_ref = payload.get("recovery", {}).get("rehydration_checkpoint_ref")
        if not checkpoint_ref:
            return False

        # Simulate cryptographic verification
        return approval_signature == "human_jules_sig_123"

    def rehydrate_and_resume(
        self,
        payload: Dict[str, Any],
        approval_signature: str,
        adjusted_boundary: Any,  # New PermissionBoundary allowing the original target_path
        remaining_actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Parses the payload, reinstantiates the simulation worker, and executes remaining steps.

        Raises:
            ValueError: If approval signature is invalid or payload structure is malformed.
        """
        # 1. Schema Validation
        if "identity" not in payload or "state" not in payload or "recovery" not in payload:
            raise ValueError("SAGE-ACT Contract Violation: Malformed audit payload.")

        # 2. Check Human Approval
        if payload["recovery"].get("human_approval_required") is True:
            if not self.verify_human_approval(payload, approval_signature):
                raise ValueError("SAGE-ACT Contract Violation: Human approval signature verification failed.")

        # 3. Snapshot Retrieval and Re-instantiation
        agent_id = payload["identity"]["agent_id"]
        # In a real system, we load snapshot data referenced by payload["state"]["active_state_snapshot_ref"]
        # Re-instantiate worker using adjusted boundaries

        # 4. Coordinated Safe Completion of remaining steps
        completed_events = []
        for action in remaining_actions:
            # Simulated execution purely on-memory
            pass

        return {
            "status": "REHYDRATION_SUCCESS",
            "checkpoint_ref": payload["recovery"]["rehydration_checkpoint_ref"],
            "rehydrated_at": datetime.now(timezone.utc).isoformat(),
            "execution_events": completed_events,
            "read_only_assertion": True
        }
```

---

## 4. Boundary Impact Analysis

- **Zero Core Changes**: Rehydration remains restricted to `sage/experimental/act/` and `tests/experimental/`. No imports of `sage/acr/`, `sage/core/`, or `sage/runtime/` are required.
- **One-Way Import Law Adherence**: AST parser tests will continue to guard against any core namespace contamination.
- **Purely Read-Only**: The proposed `GovernedAgentRehydrator` executes on-memory variables, introducing no writing operations or baseline modifications.

---

## 5. Risks and Mitigations

| Risk Description | Severity | Mitigation Strategy |
| :--- | :--- | :--- |
| **Bypassing Signature Checks**: Unauthorized or automated systems could attempt to execute rehydration runs with fake signatures. | **High** | Rigorous verification using SAGE core's attestation engines (such as `AttestationProvider`) in future promotion phases. |
| **Mismatched Snapshot Context**: The state rehydration could restore context that is stale relative to on-disk files. | **Medium** | Store file hashes in the `active_state_snapshot_ref` metadata to verify file-level consistency during recovery. |

---

## 6. Conclusion and Next Step

This research specification establishes the roadmap for the Controlled Rehydration capability.
The engineering node has successfully stopped and is currently awaiting supervisor approval.
