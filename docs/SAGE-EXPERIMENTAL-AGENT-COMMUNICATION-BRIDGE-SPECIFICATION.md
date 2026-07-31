# SAGE-ACT MILESTONE 7: EXPERIMENTAL AGENT COMMUNICATION BRIDGE SPECIFICATION

## 1. Executive Summary & Purpose
The **SAGE Experimental Agent Communication Bridge** defines a secure, non-mutating framework to facilitate, track, and validate multi-agent collaboration (such as sequential handoffs across ChatGPT, Jules, Claude, and Gemini). By introducing structured communication envelopes and programmatic handoff validation contracts, this bridge enforces strict identity verification, role-based capability boundaries, and human-in-the-loop dependencies prior to execution.

---

## 2. Core Components

### 2.1 Agent Identity Layer
The Identity Layer models collaborating agent personas:
* **`AgentIdentity`**: Captures identity properties, including:
  * `agent_id`: Pattern `^agent_[a-zA-Z0-9_]{3,64}$` (e.g., `agent_chatgpt`, `agent_jules`).
  * `name`: Descriptive name.
  * `role`: Personas (Coordinator, Executor, Analyst, Reviewer).
  * `authorized_capabilities`: List of allowed capability identifiers (e.g. `['verify_scope', 'write_code']`).
* **`AgentIdentityRegistry`**: Seeded registry holding authorized persona schemas. Unauthorized identities attempting to participate in communication handoffs are blocked instantly.

### 2.2 Communication Envelope (`AgentCommunicationEnvelope`)
All handoff payloads must be enclosed in a standardized communication envelope containing the following required properties:

| Field | Data Type | Purpose |
|---|---|---|
| `sender_id` | `str` | Authorized agent ID of the sender. |
| `receiver_id` | `str` | Authorized agent ID of the receiver. |
| `capability_id` | `str` | Target capability being utilized or requested. |
| `evidence_reference` | `str` | Reference to verified evidence packages (such as SAGE-CRC receipts). |
| `human_review_status` | `str` | Explicitly tracks review stage (`PENDING` or `APPROVED`). |
| `timestamp` | `str` | ISO 8601 UTC timestamp of envelope dispatch. |
| `execution_trace_reference` | `str` | Pointer to the active session state or execution trace log. |

### 2.3 Agent Handoff Validator (`AgentHandoffValidator`)
A programmatic validation engine executing seven strict verification checks on every handoff transition:

1. **Sender Existence Check:** Verifies `sender_id` exists inside the active `AgentIdentityRegistry`.
2. **Receiver Existence Check:** Verifies `receiver_id` exists inside the active `AgentIdentityRegistry`.
3. **Capability Authorization Check:** Confirms the requested `capability_id` is explicitly authorized for the sending agent identity.
4. **Evidence Presence Check:** Ensures a non-empty `evidence_reference` is provided.
5. **Chronological Ordering Check:** Asserts that sequential handoff timestamps are strictly monotonically increasing.
6. **Human Review Check:** Verifies the `human_review_status` is set to `"APPROVED"` or that the capability being handed off has undergone proper review before executor transition.
7. **Protected Path Rejection:** Blocks the handoff execution immediately if the capability attempts to write to or mutate files under core enclaves (`sage/runtime/`, `sage/core/`, `sage/acr/`, or `sage/agents/`).

---

## 3. Evidence Trace Capture
All multi-agent transitions must be compiled and saved to `evidence_capture/sdr_exp_002_evidence_package.json`. The package contains:
* Participating identities.
* Handoff sequence metadata.
* Validation checks run and results.
* Chronological execution log.
* Human approval decision mapping.
