# SAGE-ACT Milestone 2A: Next Capability Authorization Review

**Document Identifier:** SAGE-ACT-AR-10.0
**Classification:** Strategic Planning & Authorization review
**Status:** PROPOSED
**Author:** Jules (SAGE Governance Validation Node)
**Date:** March 2026

---

## Executive Summary

Pursuant to the SAGE-ACT Milestone 2A Next Capability Authorization Boundary Review directive, this document establishes the **formal authorization and boundary review** for SAGE-ACT's next developmental capability.

Operating strictly under SAGE's progressive lifecycle (**Authorize $\rightarrow$ Plan $\rightarrow$ Validate $\rightarrow$ Implement $\rightarrow$ Verify $\rightarrow$ Promote**), this review assesses our current validated capabilities, proposes the next logical capability block, defines strict boundaries to prevent protected layer drift, and identifies remaining architecture execution risks.

No code modifications have been made to any production or protected modules. The active baseline remains fully intact.

---

## 1. Current Validated Capability State

Our audit of the current SAGE-ACT state verifies:
* **Completed Lineage Validation:**
  * The `SessionStateTaskLinker` in `sage/experimental/act/contracts.py` is fully defined to execute format checks on session and task IDs, objective string matching against active lists, and duplicate task ID rejection.
* **Active Tests:**
  * Tests inside `tests/experimental/test_act_lineage_mapping.py` provide extensive validation for lineage mapping, objective mismatch rejection, malformed identifiers, and duplicate rejections.
* **Protected Boundary Status:** Pristine. The One-Way Import Law AST checkers are fully passing. No imports from `sage.experimental` leak into production layers.

---

## 2. Evidence Reviewed

The validation node conducted a formal review of the following six governance and planning evidence artifacts:

1. **SAGE-ACT Independent Validation Report (`docs/SAGE-ACT-MILESTONE-2A-INDEPENDENT-VALIDATION-REPORT.md`):** Confirmed implementation risks, reference-leak controls, and clock-drift buffers.
2. **SAGE-ACT Next Evolution Recommendation Report (`docs/SAGE-ACT-NEXT-EVOLUTION-RECOMMENDATION-REPORT.md`):** Identified Milestone 2B State Transaction cryptographics as the next evolution milestone.
3. **SAGE Task Continuity Audit (`docs/SAGE-TASK-CONTINUITY-AUDIT-REPORT.md`):** Verified no duplicated artifacts or redundant file creation exists.
4. **SAGE-ACT Readiness Gate Report (`docs/SAGE-ACT-MILESTONE-2A-READINESS-GATE-REPORT.md`):** Certified readiness decision and gate parameters.
5. **SAGE-ACT Pre-Implementation Authorization Review (`docs/SAGE-ACT-MILESTONE-2A-PRE-IMPLEMENTATION-AUTHORIZATION-REVIEW.md`):** Outlined strict boundaries and rollback paths.
6. **SAGE-ACT Continuity Progression Review (`docs/SAGE-ACT-MILESTONE-2A-CONTINUITY-PROGRESSION-REVIEW.md`):** Confirmed distinct progression across parallel lanes.

---

## 3. Proposed Next Capability

### 3.1 Proposed Capability: Read-Only Task-to-Decision Causal Binding (`TaskDecisionBinder`)
We propose implementing the read-only causal binding capabilities inside the `TaskDecisionBinder` class in `sage/experimental/act/contracts.py`.

### 3.2 Logical Justification
* This completing the end-to-end lineage path. While `SessionStateTaskLinker` resolves Session-to-Task links, `TaskDecisionBinder` maps Task-to-Decision causal records.
* Mapping decisions to parent tasks is a structural dependency for Milestone 2B, which implements signed state-transition recommendations and cryptographic nonces.

### 3.3 Smallest Safe Implementation Slice
* Bounded entirely within `sage/experimental/act/`. The class will accept list structures of `AgentTask` and `DecisionEntry`, normalize datetimes to UTC, verify identifier formatting, verify chronological monotonicity (decision timestamp $\ge$ task creation timestamp), and detect duplicates.

---

## 4. Implementation Boundary

The boundaries of the next capability implementation are strictly locked:

* **Allowed Scope:**
  * Modifying `TaskDecisionBinder` inside `sage/experimental/act/contracts.py`.
  * Creating test assertions inside `tests/experimental/test_act_lineage_mapping.py`.
* **Forbidden Scope:**
  * Any modification to `sage/runtime/`, `sage/core/`, or `sage/acr/`.
  * Modifying container, Docker, or Render setup configurations.
  * Attempting to canonicalize or promote experimental code into core registries.

---

## 5. Validation Requirements

Any implemented code for this capability slice must successfully satisfy four validation gates:

* **Gate 1: Format Checks:** Raise `ValueError` with `"SAGE-ACT Contract Violation:"` on malformed decision IDs.
* **Gate 2: Chronological Ordering:** Enforce chronological consistency:
  $$T_{decision} \ge T_{task} - \delta_{drift}$$
  where $\delta_{drift} \le 5\text{ seconds}$ represents maximum acceptable network clock drift.
* **Gate 3: Duplicate Rejection:** Automatically detect and reject duplicate decision payloads.
* **Gate 4: Isolation checks:** Pytest AST parsing checks must continue to confirm absolute unidirectional import isolation.

---

## 6. Evidence Requirements

The successful completion of this slice requires generating:
* **`docs/SAGE-ACT-MILESTONE-2-TASK-DECISION-CAUSAL-BINDER-RECEIPT.md`**: Detailing code changes, test metrics, and verification traces.

---

## 7. Risks and Mitigations

* **In-Memory Model Mutations:** Passed Python objects can be mutated in place.
  * *Mitigation:* Perform immediate deep-copying on all arguments inside the validation entry point.
* **Clock Drift Anomalies:** Disparate server runtimes can cause clock desynchronization.
  * *Mitigation:* Apply UTC normalization and provide a 5-second leeway buffer ($\delta_{drift}$) for timing checks.

---

## 8. Recommended Next Checkpoint

```
[M2A NCP Review] ──► [Milestone 2A Extension Implementation] ──► [Milestone 2A Integration Gate]
    (CURRENT)                    (SESSION 1)                     (160+ PYTEST RUN)
```

The validation node issues a status of **AUTHORIZED FOR IMPLEMENTATION** for the `TaskDecisionBinder` capability under the specified boundary. Active coding may proceed.
