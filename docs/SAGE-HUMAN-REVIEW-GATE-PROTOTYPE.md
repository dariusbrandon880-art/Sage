# SAGE Human Review Gate Prototype

This document presents the design specification, structural schema, operational workflows, and future integration plans for the **SAGE Human Review Gate Prototype**. It serves as the final manual and cognitive checkpoint in SAGE's Capability Evolution Governance Framework, programmatically validating reviewer identity and notes before allowing any capability promotion.

This prototype resides strictly within experimental boundaries (`sage/experimental/act/contracts.py`) to safeguard core production directories from premature mutations.

---

## 1. Purpose

The core objective of the **SAGE Human Review Gate** is to:
- Establish a rigorous, manual authorization checkpoint prior to any capability lifecycle movement.
- Provide a non-bypassable programmatic gate that records reviewer identities, signoff notes, and decisions, preventing anonymous or undocumented capability activations.
- Ensure all promotions are fully validated, chronological, and structurally traced back to concrete evidence receipts.

---

## 2. Review Schema

Every completed Human Review Audit Trace is a structured document consisting of exactly nine required fields:

| Field Name | Expected Type | Format & Constraint | Description |
| :--- | :--- | :--- | :--- |
| **`review_id`** | `str` | Must match pattern `^rev_[a-zA-Z0-9_]{8,64}$` | Unique identifier. Defaults to a secure 16-character SHA-256 hash. |
| **`receipt_id`** | `str` | Must match pattern `^rcpt_[a-zA-Z0-9_]{8,64}$` | Unique identifier of the associated Capability Evidence Receipt. |
| **`capability_id`** | `str` | Must match pattern `^cap_[a-zA-Z0-9_]{3,64}$` | Unique identifier of the capability under review. |
| **`reviewer_identity`** | `str` | Non-empty string | The authenticated name or role of the human reviewer (e.g., `supervisor_v1`). |
| **`review_decision`** | `str` | Must be one of: `approved`, `rejected` | The explicit choice submitted by the reviewer. |
| **`review_notes`** | `str` | Non-empty string | Detailed rationale or audit findings supporting the decision. |
| **`timestamp`** | `str` | ISO 8601 UTC timestamp format | Date and time when this review gate was executed. |
| **`validation_status`** | `str` | One of: `VALIDATED`, `REJECTED` | Resolved validation state resulting from the decision. |
| **`archive_destination`** | `str` | E.g. `Main Archive/cap_..._review_gate.json` | Designate storage path within the immutable archive directory tree. |

---

## 3. Approval and Rejection Workflows

The Human Review Gate processes incoming reviews through two deterministic pathways:

### 3.1 Approval Workflow
1. **Intake:** The reviewer submits an `approved` decision on a valid evidence receipt, along with supporting notes.
2. **Attestation Compilation:** The `validation_status` is resolved to `VALIDATED`.
3. **Trace Generation:** The system returns a finalized trace showing `audit_trail_valid=True`, certifying compliance.
4. **Promotion Preparation:** Under core integration rules, the system prepares the associated capability for promotion from `PROPOSED` to `VALIDATED` inside the Master Index registry.

### 3.2 Rejection Workflow
1. **Intake:** The reviewer submits a `rejected` decision on a valid evidence receipt, specifying missing requirements or failed parameters in the notes.
2. **Attestation Compilation:** The `validation_status` is resolved to `REJECTED`.
3. **Trace Generation:** The system returns a finalized trace showing `audit_trail_valid=True` but flagging the rejection state.
4. **Halt & Log:** The capability transition is blocked, preventing any change in its index registry state and leaving it flagged for refactoring or further research gates.

---

## 4. Evidence Lifecycle Alignment

The prototype represents the culmination of SAGE’s governance lifecycle flow:

$$\text{Research} \rightarrow \text{Validation} \rightarrow \text{Evidence} \rightarrow \text{Human Review} \rightarrow \text{Master Archive}$$

- **Validation Gate:** Standard programmatic checks verify capability syntax.
- **Evidence Gate:** The validator outputs an immutable Evidence Receipt.
- **Human Review Gate:** An authorized human reviewer inspects the evidence, records findings, and assigns a signed approval/rejection state.
- **Master Archive Gate:** Upon human review approval, the validated capability passport and its review audit trace are stored permanently inside the Master Archive.

---

## 5. Pass / Fail Validation Behavior

The gate acts as a strict programmatic filter:

- **Pass Outcomes:** When provided with a valid evidence receipt, an allowed decision choice, and non-empty notes, the gate generates a formatted read-only audit dictionary.
- **Fail Outcomes:** The gate raises a `ValueError` if:
  - Required fields are missing from the input evidence receipt structure.
  - The review notes are empty or contain only whitespace.
  - The review decision lies outside the allowed set of `['approved', 'rejected']`.

---

## 6. Future Integration Requirements

To transition the Human Review Gate from experimental boundaries into active production:
1. **Command Center UI Integration:** Provide a visual verification dashboard inside SAGE's Command Center for supervisors to view receipts and easily submit review decisions.
2. **REST API Interface:** Implement a REST route `/promote/review` in `sage/api.py` to allow human reviews to be submitted via authenticated JSON payloads.
3. **Immutable Verification Logs:** Bind generated review audit traces to SAGE's internal blockchain or ledger systems (such as SAGE-MAT) to establish non-repudiable proof of supervisor signoff.
