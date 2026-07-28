# SAGE Agent Continuity Tree (SAGE-ACT) Milestone 3 Proposal

**Document Identifier:** SAGE-ACT-MP-3.0
**Classification:** Experimental Milestone Proposal
**Status:** PROPOSED
**Author:** Jules (SAGE Engineering Node)
**Date:** March 2026

---

## 1. Capability Objective

The objective of SAGE-ACT Milestone 3 is to implement the **Stateless Context Rehydration Validation Scaffold** inside the experimental Multi-Agent Continuity Tree boundary.

This milestone introduces a stateless, read-only **`GovernedAgentRehydrator`** class. Its job is to ingest a verified **CMAPS v1.0** audit payload, verify its cryptographic attestation block, validate the consistency of its chronological state timeline, and generate a validated, rehydrated memory snapshot of the agent's computational state prior to resuming execution.

This scaffold operates strictly in a read-only, non-mutating manner under experimental isolation, providing a zero-risk preview of secure context recovery.

---

## 2. Enterprise Problem Addressed

In enterprise agent deployments, agent executions frequently crash or pause due to network timeouts, rate limits, or unexpected API exceptions. Standard recovery mechanisms simply restart the agent with its raw memory or last known database record.

This introduces a critical security vulnerability: **State Hijacking and Memory Poisoning**.
If an attacker compromises the underlying database or intercepts the transit layer during a crash, they can inject malicious variables, alter the step counter, or spoof decision records to elevate privileges when the agent rehydrates and resumes.

**Enterprise Solution:** SAGE requires a cryptographically validated rehydration gate. By verifying the attestation signature and chronological consistency of the CMAPS audit payload, SAGE can programmatically guarantee that the state being rehydrated is pristine, untampered, and logically contiguous, preventing hijacked state execution.

---

## 3. Implementation Scope

The implementation is strictly bounded within the experimental namespace (`sage/experimental/act/`):

1. **`GovernedAgentRehydrator` Contract Class:**
   * **`verify_payload_integrity(payload: Dict[str, Any]) -> bool`:** Validates HMAC signature matches the payload hash and the nonce is fresh.
   * **`extract_rehydration_context(payload: Dict[str, Any]) -> Dict[str, Any]`:** Reconstructs the agent's variables, step counter, active objective, and parent-child task lineages from the verified payload.
2. **STATEL_REHYD Metadata Structure:** Defines the output schema of the verified rehydration state dictionary.
3. **Export Verification:** Expose the rehydrator class cleanly in `sage/experimental/act/__init__.py`.

---

## 4. Files Expected to Change

| File Path | Type | Action | Description / Purpose |
| :--- | :--- | :--- | :--- |
| `sage/experimental/act/rehydrator.py` | Python Code | Create | Implements the read-only, stateless `GovernedAgentRehydrator` class. |
| `sage/experimental/act/__init__.py` | Python Code | Overwrite | Exports the new rehydrator contract. |
| `tests/experimental/test_cross_model_audit_schema.py` | Python Test | Overwrite | Appends unit tests validating rehydration parsing, signature checks, and negative path injection blocks. |
| `Main Archive/INDEX.md` | Markdown Index | Overwrite | Registers this proposal under `PROPOSED` state. |

---

## 5. Validation Strategy

Validation will follow SAGE’s rigorous multi-layered testing standards:

* **Positive Path Verification:** Ingestion of a completely valid CMAPS v1.0 payload successfully rehydrates into a validated state dictionary containing the correct step counter and variable states, returning `validation_status: "REHYDRATION_VERIFIED"`.
* **Negative Path Verification (Adversarial):**
  * **Signature Tampering:** Inject payloads with modified variables or step counters but keeping the original signature, confirming the validator rejects the run with a `ValueError`.
  * **Replay Nonce Check:** Inject a payload containing a nonce that already exists in SAGE’s ledger to block replay attacks.
  * **Format Injections:** Pass invalid hex keys or non-conforming step formats, ensuring strict regex rejection.
* **Isolation Verification:** Running the AST import checking suite to ensure that no code in core directories imports or links to `sage/experimental/act/rehydrator.py` (One-Way Import Law).

---

## 6. Rollback Plan

* **Zero-Downtime Reversion:** A full rollback is achieved simply by reverting the experimental ACT directory via standard git commands and deleting `sage/experimental/act/rehydrator.py`.
* **Zero System Risks:** Because the scaffold is entirely read-only, stateless, and non-mutating, it touches no databases, changes no core services, and carries **absolute zero risk** of system corruption or production downtime.

---

## 7. Demonstration Value

For enterprise stakeholders, Milestone 3 demonstrates SAGE’s capability to enforce **unbreakable execution continuity**:
1. **Verifiable State Recovery:** Proof that SAGE can statelessly and securely recover from network or model-level crashes.
2. **Cryptographic Defense:** Demonstrating live interception of altered state-injection attacks.
3. **Audit Trail Continuity:** Proving that the resumed execution maintains perfect lineage trace integrity from the original root session.

---

## 8. Boundary Audit

* **Strict Isolation:** All code and tests are fully confined within `sage/experimental/act/` and `tests/experimental/`.
* **No Core Mutations:** Directories `sage/runtime/`, `sage/core/`, and `sage/acr/` are 100% protected and remain completely unchanged.
* **No Schema Drift:** This milestone does not modify CMAPS v1.0. It strictly acts as a consumer of the existing schema, avoiding unnecessary schema expansion.
