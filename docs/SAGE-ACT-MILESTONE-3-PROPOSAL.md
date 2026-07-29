# SAGE-ACT Milestone 3 Capability Proposal: Stateless Controlled Rehydration

**Document Identifier:** SAGE-ACT-M3P-1.0
**Classification:** Validated Planning & Capability Proposal
**Status:** PROPOSED
**Author:** Jules (SAGE Engineering Node)
**Date:** March 2026

---

## 1. Capability Objective

The objective of SAGE-ACT Milestone 3 is to establish a read-only, stateless validation scaffold (`GovernedAgentRehydrator`) capable of parsing, verifying, and dry-run rehydrating an agent's computational state from an authenticated `SageAgentReliabilityAuditPayload`. This capability ensures that a failed or intercepted agent execution can be safely analyzed, validated for cryptographic and chronological integrity, and verified for state rehydration without executing real-world side effects or mutating core production databases.

---

## 2. Problem Addressed

When an autonomous agent violates a permission boundary or encounters a critical infrastructure failure, its execution is gracefully intercepted, and its active state is serialized (as established in SAGE Agent Reliability Layer v1 Intercept).

However, currently:
1. **No Safe Dry-Run Path:** There is no isolated mechanism to verify whether a saved state snapshot can be safely loaded and re-run.
2. **Cryptographic & Nonce Validation Gap:** There is no stateless check to guarantee that the snapshot payload has not been tampered with, forged, or replayed.
3. **Lineage Disconnection:** The system cannot guarantee that the rehydrated state's chronological markers and decision chains align with the parent session’s active objectives prior to actual execution resumption.

Milestone 3 solves these problems by providing a standardized, zero-trust validation gate for serialized state rehydration.

---

## 3. Smallest Safe Experimental Scope

To maintain absolute production safety, the proposed implementation scope is restricted exclusively to:
- **Stateless Analysis:** No database writes, active API dispatches, or state persistence.
- **Strict Read-Only Verification:** Input payloads are parsed, verified, and dry-run mapped in-memory.
- **Experimental Isolation:** All code is confined strictly to the experimental `sage/experimental/act/` namespace.
- **Zero Runtime side-effects:** The components will not hook into, intercept, or modify active production workflows or agent runtime dispatchers.

---

## 4. Expected Files Affected

All proposed modifications are restricted to the experimental boundary:

### Created Files:
- `sage/experimental/act/rehydrator.py` – Implements the `GovernedAgentRehydrator` class and dry-run rehydration contracts.
- `tests/experimental/test_act_rehydrator.py` – Verifies stateless rehydration validation, signature/replay defenses, and chronological checks.

### Modified Files (Registration Only):
- `sage/experimental/act/__init__.py` – Exports the new `GovernedAgentRehydrator` class.
- `Main Archive/INDEX.md` – Registers this proposal and the future implementation receipt.

---

## 5. Evidence Generated

The implementation of Milestone 3 will generate the following evidence packages to prove readiness:
1. **Verification Test Reports:** Complete pytest logs proving successful execution of the new rehydrator test suite.
2. **Cryptographic Verification Logs:** Simulated audit traces demonstrating successful signature check runs and rejection of tampered/unauthenticated payloads.
3. **Boundary Compliance Report:** Static AST import logs demonstrating 100% adherence to the One-Way Import Law (zero imports from `sage/experimental/` to core/production).
4. **Milestone 3 Implementation Receipt:** A formalized markdown receipt under `docs/SAGE-ACT-MILESTONE-3-IMPLEMENTATION-RECEIPT.md`.

---

## 6. Validation Strategy

The proposed `tests/experimental/test_act_rehydrator.py` suite will programmatically enforce the following validation gates:

| Gate ID | Name | Validation Criteria |
| :--- | :--- | :--- |
| **VAL-M3-01** | Stateless Parsing | Confirms successful reconstruction of an agent's execution state from a valid JSON-compliant payload. |
| **VAL-M3-02** | Signature Verification | Validates that payloads contain authentic, untampered signatures, raising validation errors on key mismatches. |
| **VAL-M3-03** | Replay & Nonce Defense | Blocks rehydration requests containing stale nonces or signatures that have already been processed in the current session. |
| **VAL-M3-04** | Chronological Alignment | Verifies that the checkpoint's internal timestamps are strictly monotonic and succeed all session task creation times. |
| **VAL-M3-05** | Dry-Run Simulation | Asserts that "dry-run" execution performs only memory operations and makes zero disk writes or database modifications. |

---

## 7. Rollback Procedure

Since all code is fully isolated within the experimental directory, rollback is 100% safe and simple:
1. **Code Rollback:** Delete `sage/experimental/act/rehydrator.py` and `tests/experimental/test_act_rehydrator.py`.
2. **Export Reversion:** Restore `sage/experimental/act/__init__.py` to remove `GovernedAgentRehydrator` from `__all__`.
3. **Git Restore:** Run `git checkout main -- sage/experimental/act/__init__.py` to return the branch to the pristine Milestone 2A state.

---

## 8. Security and Isolation Considerations

- **Strict One-Way Import Law:** The `GovernedAgentRehydrator` must only import from standard Python libraries, other experimental contracts, and standard agent/task Pydantic model definitions. Direct imports from production control loops are strictly prohibited.
- **Input Sanitization:** The parser treats all input payloads as zero-trust, validating fields, value lengths, and types strictly before constructing local models.
- **No Side-Effects Guarantee:** Any method simulating step resumption must enforce that the output event is marked as `status=AgentTaskState.SIMULATED` or `read_only_assertion=True`.

---

## 9. Capability Tree Placement

Milestone 3 sits at the bridge of our failure-recovery capability tree:

```
[M2A: Lineage Validation] (VALIDATED)
            │
            ▼
[v1 Intercept Foundation] (VALIDATED)
            │
            ▼
[M3: Stateless Rehydration] (PROPOSED - CURRENT)
            │
            ▼
[M4: Controlled Dry-Run Executor] (FUTURE)
```

By verifying that failed computational states can be reconstructed and validated statelessly, we establish the necessary prerequisites for Milestone 4 (where a restricted dry-run executor will simulate safe recovery runs of validated snapshots).

---

## 10. Governance Transition Gate Requirements

To transition from **PROPOSED** to **AUTHORIZED FOR IMPLEMENTATION**, this proposal requires:
1. **Supervisor Review & Approval:** Sign-off from the supervising human/agent authority.
2. **PR Compliance Gate Pass:** Absolute zero-drift confirmation on all 188 baseline platform tests.
3. **Master Archive Indexing:** Official registration as a `PROPOSED` planning artifact in the Main Archive.
