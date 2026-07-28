# SAGE Agent Reliability Layer v1: Audit Payload Schema Proposal

**Document Identifier:** SAGE-ARL-APS-1.0
**Classification:** Experimental Specification Document
**Status:** PROPOSED
**Author:** Jules (SAGE Engineering Node)
**Date:** March 2026

---

## 1. Executive Summary

This document proposes the formal **SAGE Agent Reliability Layer v1 Audit Payload Schema**.
Designed to prepare the system for **Graceful Intercept and Rehydration**, this JSON-compatible, machine-validatable schema provides an enterprise-ready structure to capture, track, and rehydrate autonomous workflows that experience failure.

This schema connects directly with our read-only `TaskDecisionCausalBinder` and `SessionStateTaskLinker` contracts, creating a comprehensive audit payload that maps failed execution steps, their context, their chronological dependencies, and recovery checkpoints.

---

## 2. Proposed JSON Schema Specification

The JSON-compatible schema definition for the SAGE Agent Reliability Audit Payload v1 is defined below.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SageAgentReliabilityAuditPayload",
  "type": "object",
  "required": [
    "identity",
    "state",
    "failure_event",
    "decision_lineage",
    "recovery"
  ],
  "properties": {
    "identity": {
      "type": "object",
      "required": [
        "agent_id",
        "task_id",
        "session_id",
        "workflow_id"
      ],
      "properties": {
        "agent_id": {
          "type": "string",
          "pattern": "^agent_[a-zA-Z0-9_\\-]+$",
          "description": "Unique governed identifier of the agent actor."
        },
        "task_id": {
          "type": "string",
          "pattern": "^task_[a-zA-Z0-9_\\-]+$",
          "description": "Underlying task identifier within SAGE workflows."
        },
        "session_id": {
          "type": "string",
          "pattern": "^session_[a-zA-Z0-9_\\-]+$",
          "description": "High-level cognitive session identifier."
        },
        "workflow_id": {
          "type": "string",
          "pattern": "^workflow_[a-zA-Z0-9_\\-]+$",
          "description": "Orchestrated workflow trace identifier."
        }
      }
    },
    "state": {
      "type": "object",
      "required": [
        "current_task_step",
        "previous_steps",
        "active_state_snapshot_ref"
      ],
      "properties": {
        "current_task_step": {
          "type": "string",
          "description": "Name or identifier of the failing task step."
        },
        "previous_steps": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["step_name", "completed_at", "status"],
            "properties": {
              "step_name": { "type": "string" },
              "completed_at": { "type": "string", "format": "date-time" },
              "status": { "type": "string", "enum": ["COMPLETED", "SKIPPED"] }
            }
          },
          "description": "Ordered checklist of completed steps prior to failure."
        },
        "active_state_snapshot_ref": {
          "type": "string",
          "pattern": "^snapshot_[a-zA-Z0-9_\\-]+$",
          "description": "Reference key to the persisted rehydration snapshot in database storage."
        }
      }
    },
    "failure_event": {
      "type": "object",
      "required": [
        "failure_type",
        "timestamp",
        "originating_component",
        "external_dependency_status"
      ],
      "properties": {
        "failure_type": {
          "type": "string",
          "enum": ["BOUNDARY_VIOLATION", "TIMEOUT", "DEPENDENCY_OFFLINE", "ASSERTION_FAILED", "RESOURCES_EXHAUSTED", "UNKNOWN"],
          "description": "Categorized reason for the failure event."
        },
        "timestamp": {
          "type": "string",
          "format": "date-time",
          "description": "Exact timestamp of the failure, standardized to ISO-8601 UTC."
        },
        "originating_component": {
          "type": "string",
          "description": "Namespace or class name of the failing module (e.g. 'sage.experimental.act.agent_runner')."
        },
        "external_dependency_status": {
          "type": "object",
          "additionalProperties": { "type": "string" },
          "description": "Active connection states of target external endpoints (e.g., 'workspace_api': 'OFFLINE')."
        }
      }
    },
    "decision_lineage": {
      "type": "object",
      "required": [
        "causal_binder_ref",
        "causal_chain",
        "underlying_decisions"
      ],
      "properties": {
        "causal_binder_ref": {
          "type": "string",
          "pattern": "^validation_status_.*$",
          "description": "Reference key from TaskDecisionCausalBinder run."
        },
        "causal_chain": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Ordered dependency array of decisions or events leading directly to the current state."
        },
        "underlying_decisions": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["decision_id", "decision_type", "timestamp"],
            "properties": {
              "decision_id": { "type": "string", "pattern": "^(decision|proposal)_[a-zA-Z0-9_\\-]+$" },
              "decision_type": { "type": "string", "enum": ["architectural", "technical", "process", "strategic"] },
              "timestamp": { "type": "string", "format": "date-time" }
            }
          },
          "description": "Chronological audit records of decision items verified by TaskDecisionCausalBinder."
        }
      }
    },
    "recovery": {
      "type": "object",
      "required": [
        "recovery_possible",
        "human_approval_required",
        "rehydration_checkpoint_ref"
      ],
      "properties": {
        "recovery_possible": {
          "type": "boolean",
          "description": "Indicates whether the task can be safely rehydrated."
        },
        "human_approval_required": {
          "type": "boolean",
          "description": "Blocks autonomous rehydration until a verified human signature is provided."
        },
        "rehydration_checkpoint_ref": {
          "type": "string",
          "pattern": "^checkpoint_[a-zA-Z0-9_\\-]+$",
          "description": "Reference ID for the last verified state checkpoint."
        }
      }
    }
  }
}
```

---

## 3. Product-Validation Schema Analysis

### 3.1. Why This is the Next Logical Dependency
In SAGE’s evolution roadmap, validation mapping (`contracts.py`) and simulated execution (`agent_runner.py`) have been established. However, in enterprise environments, autonomous agents frequently encounter failures (e.g., connection dropouts, rate limit blocks, boundary interceptions).

To transition from mere *simulation execution* to *reliable orchestration*, the system must be able to log and serialise failure states. Designing this schema is the foundational dependency for the **SAGE Agent Reliability Layer v1**—providing the exact data structure that recovery and rehydration systems must consume.

### 3.2. How It Supports the Agent Reliability Layer
The SAGE Agent Reliability Layer depends on two core patterns:
1. **Graceful Intercept**: Intercepting path and action boundary infractions safely inside `GovernedAgentSimWorker` and generating a serialised failure trace.
2. **Rehydration**: Reading a serialized checkpoint record and reinstantiating a new agent sim worker exactly at the failing step with the original session context.

This schema integrates these two halves. When `GovernedAgentSimWorker` intercepts a boundary violation, it generates this precise payload. The rehydration module then parses this payload, checks the human approval requirements, retrieves the referenced `snapshot_ref`, and resumes execution safely.

### 3.3. How It Enables Future Demo Capability
For stakeholders, this schema enables a compelling **Rehydration Demo**:
- **Setup**: Run a simulated agent on a workflow. Intercept the agent purposefully with a mock network timeout or prohibited action.
- **Fail Stage**: Generate the `SAGE-ARL-APS` JSON payload in real time and display it on an enterprise admin dashboard showing the causal decision chain and the active failure.
- **Approval Stage**: Simulate a human clicking "Approve Rehydration", signing the `rehydration_checkpoint_ref`.
- **Recovery Stage**: Reload the workflow purely on-memory and show successful completion of the remaining workflow steps, validating autonomous continuity and zero-touch error recovery.

---

## 4. Risks and Mitigation

| Risk Description | Severity | Mitigation Strategy |
| :--- | :--- | :--- |
| **Tampering with Recovery Information**: An attacker or rogue process alters the `recovery_possible` or `human_approval_required` flags to bypass authorization controls. | **High** | Protect the audit payload using standard SAGE Cryptographic Attestation. Sign the schema contents using `CryptographicAttestationProvider` and verify the signature prior to rehydration. |
| **Clock Mismatch during Chronological checks**: Originating component clock drifts could mismatch with external dependency statuses. | **Medium** | Standardize all timestamps to timezone-aware UTC format using strictly parsed ISO-8601 strings, handled dynamically by SAGE contracts. |
| **Deserialization Name Errors**: Pydantic and raw dict format differences in nested objects (like `DecisionEntry` vs. raw dict) could raise attribute errors. | **Medium** | Support dual dynamic field lookup (`getattr`/`hasattr` and dictionary subscripting) to standardise parsing interfaces. |

---

## 5. Conclusion and Next Step

This schema completes the planning and design boundary of the SAGE Agent Reliability Layer v1. In strict compliance with SAGE governance guidelines, we have **stopped** and are awaiting formal supervisor review before any implementation or promotion activity occurs.
