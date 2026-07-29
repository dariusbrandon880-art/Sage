# SAGE Agent Continuity Tree (SAGE-ACT) Milestone 5 Proposal

**Document Identifier:** SAGE-ACT-MP-5.0
**Classification:** Experimental Milestone Proposal
**Status:** PROPOSED
**Author:** Jules (SAGE Engineering Node)
**Date:** March 2026

---

## 1. Executive Summary

Having successfully designed and verified the SAGE Cross-Model Audit Payload Schema (CMAPS v1.0), validated read-only context rehydration (Milestone 3), and simulated stateless dry-run execution (Milestone 4), SAGE has completed the foundational elements of its **Graceful Intercept and Recovery Loop**.

The next highest-value gap in the SAGE Agent Continuity Tree is the **multi-step recovery audit loop**. When an agent undergoes multiple sequential failures and rehydrations across a session, there is a risk of compounding state drift, session-key fragmentation, or replay vulnerability across recovery iterations.

This proposal defines **Milestone 5: Stateless Recovery Attestation & Receipt Chain Auditor (SAGE-ACT-SRACA)**. This component validates the structural and cryptographic integrity of a chain of recovery attestation receipts (using SAGE's existing `EASReceiptChain` concepts) to prove that a multi-hop rehydration session is free of cycle loops, sequence splits, or unauthorized state drift.

---

## 2. Capability Assessment

### 2.1. Current Capabilities (The Foundation)
* **CMAPS v1.0 Validator:** Structural, chronological, and relational integrity of individual execution blocks.
* **GovernedAgentRehydrator (Milestone 3):** Cryptographic verification of single-hop rehydration snapshots with secure nonce tracking.
* **GovernedAgentExecutor (Milestone 4):** Stateless simulation preview of agent execution resumption.

### 2.2. The Gap (Multi-Hop Recovery Drift)
Currently, SAGE can rehydrate and simulate a single recovery step. However, if an agent fails repeatedly (e.g., Step 5 -> Recover -> Fail at Step 8 -> Recover -> Fail at Step 12), there is no programmatic layer to verify the **continuity of the recovery lineage itself**. An attacker could try to splice a stale checkpoint from a different run branch or introduce a chronological loop across separate recovery steps.

### 2.3. Proposed Capability: SAGE-ACT-SRACA
The Stateless Recovery Attestation & Receipt Chain Auditor (`RecoveryReceiptChainAuditor`) will:
1. Parse a sequential list of recovery attestation receipts.
2. Verify that each receipt in the chain refers back to the cryptographic hash of the prior recovery receipt (forming a backward-linked hash chain).
3. Confirm that the total accumulated drift across the recovery hops (e.g., changes in tokens, cumulative step counter offsets) does not exceed defined threshold limits.

---

## 3. Dependency Review

This capability relies on existing experimental and core structures:
* **CMAPS v1.0 payloads (`docs/SAGE-CROSS-MODEL-AUDIT-PAYLOAD-SCHEMA.md`):** Uses the `recovery_checkpoints` and `attestation` structures.
* **`SessionState` (`sage/acr/session/session_state.py`):** Matches the session ID and references the initial validated session state.
* **HMAC Cryptographic Primitives:** Shares the signature verification model implemented in `GovernedAgentRehydrator` (Milestone 3).

---

## 4. Smallest Safe Experimental Scope

To maintain SAGE's zero-risk policy, the auditor will be implemented as a read-only, stateless class (`RecoveryReceiptChainAuditor`) strictly confined within the experimental namespace `sage/experimental/act/`:

* **Input:** A list of CMAPS attestation receipt dictionaries representing the recovery hops.
* **Internal Logic:**
  * Walk the receipt list and verify the backward-linked checksums (`current_receipt.parent_hash == prior_receipt.current_hash`).
  * Enforce monotonic progress on session step counters across recovery iterations.
  * Check the accumulated drift of state variables against strict security constants.
* **Output:** An audit result dictionary: `{"chain_status": "AUDIT_VERIFIED", "verified_hops": 3, "accumulated_drift": 0.04}`.

---

## 5. Evidence Requirements & Expected Impact

The implementation will introduce/modify the following files under absolute experimental isolation:

| File Path | Action | Role |
| :--- | :--- | :--- |
| `sage/experimental/act/chain_auditor.py` | Create | Implements the read-only, stateless `RecoveryReceiptChainAuditor` class. |
| `sage/experimental/act/__init__.py` | Overwrite | Exports the new chain auditor. |
| `tests/experimental/test_cross_model_audit_schema.py` | Overwrite | Appends robust unit tests validating receipt chain integrity. |
| `Main Archive/INDEX.md` | Overwrite | Registers this proposal as `PROPOSED`. |

---

## 6. Validation Strategy

The validator contract will be tested against both positive and highly adversarial scenarios:
* **Attestation Tampering:** Modifying an intermediate recovery receipt's hash or step counter, confirming that the auditor immediately identifies the break in the hash chain.
* **Branch Splice Attack:** Attempting to inject a recovery receipt from a parallel session, ensuring that the session ID validation rejects it.
* **Step-Counter Reversion:** Simulating a recovery step that attempts to roll back the step counter to an earlier step without an authorized rollback reference.
* **One-Way Import Compliance:** AST walk tests verifying that `chain_auditor.py` has zero imports of protected core files, adhering to the One-Way Import Law.

---

## 7. Rollback Plan

* **Zero Mutation Risk:** Reverting the changes involves standard git checkouts of modified experimental files and deleting `sage/experimental/act/chain_auditor.py`.
* **Zero Run-Time Coupling:** Since the component is entirely stateless, read-only, and confined to the experimental namespace, it is impossible for its implementation to degrade production performance or cause regressions to the active system.

---

## 8. Authorization Gate

This proposal is submitted to the supervisor node for review. No implementation code or mock testing of SAGE-ACT-SRACA will be executed until authorization is explicitly granted.
