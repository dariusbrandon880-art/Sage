# SAGE Capability Passport Validation Prototype

This document outlines the purpose, schema, validation behavior, and execution trace of the **SAGE Capability Passport Validator Prototype**. It represents SAGE’s first controlled engineering validation prototype, establishing the foundation of the **"No Orphan Capability"** rule inside `sage/experimental/act/contracts.py`.

---

## 1. Validation Purpose

Under SAGE’s Capability Tree Health Assessment and Governance Framework, new agent and runtime capabilities are prohibited from entering core development without a registered Capability Passport.
The purpose of the **SAGE Capability Passport Validator** is to:
- Enforce the "No Orphan Capability" rule programmatically.
- Verify that every capability is formally linked to an active purpose, a clear validation strategy, a valid documentation evidence file, and a registered list of dependency capabilities.
- Programmatically check that high-trust lifecycle states (`validated`, `canonical`) cannot be reached without verified human supervisor approval.

---

## 2. Capability Passport Schema Rules

The validator prototype expects a structured dictionary containing the following eight required fields:

| Field Name | Expected Type | Format & Constraint | Description |
| :--- | :--- | :--- | :--- |
| **`capability_id`** | `str` | Must match pattern `^cap_[a-zA-Z0-9_]{3,64}$` | Unique identifier of the capability. |
| **`name`** | `str` | Non-empty string | Human-readable name of the capability. |
| **`purpose`** | `str` | Non-empty string | Explanation of why this capability is needed. |
| **`lifecycle_state`** | `str` | One of: `proposed`, `validated`, `archive_candidate`, `canonical` | The active development stage of the capability. |
| **`validation_strategy`** | `str` | Non-empty string | Concrete plan to verify this capability's behavior. |
| **`evidence_path`** | `str` | Must start with `docs/` or `evidence/` | File path pointing to the active validation evidence document. |
| **`dependencies`** | `list[str]` | List of valid capability identifiers (e.g., `cap_...`) | List of capabilities this capability directly relies upon. |
| **`human_signoff`** | `dict` | Must contain: `signer`, `timestamp`, `approved` (bool) | Explicit record of human supervisor verification. |

---

## 3. Pass / Fail Validation Behavior

The validator executes deterministic validation checks and exhibits the following behaviors:

### 3.1 Validation Pass Requirements
- All eight required fields are present.
- All format, pattern, and directory path constraints are met.
- **Monotonicity Rule Checked:** If `lifecycle_state` is set to `validated` or `canonical`, the inner `human_signoff.approved` boolean must be `True`.

### 3.2 Validation Fail Trigger Conditions
The validator raises a `ValueError` indicating a contract violation if:
- Any top-level field (e.g., `purpose`, `evidence_path`) is missing or of an invalid type.
- The `capability_id` lacks the required `cap_` prefix or contains invalid characters.
- The `evidence_path` points outside the approved documentation directories (`docs/` or `evidence/`).
- The `dependencies` elements are not formatted as valid capability IDs.
- **Unauthorized State Transition Detected:** The `lifecycle_state` is set to `validated` or `canonical` but human approval is false (`approved = False`). This programmatically blocks un-signed capabilities from claiming validated status.

---

## 4. Evidence Output Format

Upon successful execution, the validator generates a read-only metadata validation result dictionary of the following format:

```json
{
  "capability_id": "cap_sdr_sim_engine",
  "validated_at": "2026-03-31T17:45:00.123456+00:00",
  "validation_status": "PASSPORT_VALIDATED",
  "approved": true,
  "read_only_assertion": true
}
```

This output acts as a structured attestation that can be parsed by automated build pipelines or recorded inside SAGE’s internal event archives to verify compliance.

---

## 5. Future Integration Requirements

The prototype currently resides within experimental boundaries (`sage/experimental/act/`). To fully transition this capability into core operations:
1. **Validation Middleware Integration:** Hook `CapabilityPassportValidator` into the operational REST endpoint paths `/validate` and `/promote/validated` in `sage/api.py`.
2. **Build-Time Verification:** Run the passport validator as a pre-merge Git hook, preventing pull requests from merging if a modified capability lacks an approved and validated passport.
3. **Automated Traceability Map:** Use the validation output artifacts to dynamically rebuild SAGE’s runtime knowledge and capability dependency graph.
