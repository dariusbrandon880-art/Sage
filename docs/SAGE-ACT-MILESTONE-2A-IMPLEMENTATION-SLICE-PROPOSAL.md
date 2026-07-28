# SAGE-ACT Milestone 2A: Next Implementation Slice Proposal

**Document Identifier:** SAGE-ACT-ISP-9.0
**Classification:** Pre-Implementation Architectural Proposal
**Status:** PROPOSED
**Author:** Jules (SAGE Architecture Review Node)
**Date:** March 2026

---

## Executive Summary

Pursuant to the SAGE-ACT Milestone 2A Next Implementation Slice Planning Review Authorization directive, this document establishes the **formal implementation slice proposal** for the next authorized SAGE-ACT Milestone 2A expansion.

This proposal maps the capability, dependencies, expected file impact, testing parameters, evidence requirements, and rollback strategies. Consistent with the authorized workflow lifecycle (**Authorize $\rightarrow$ Plan $\rightarrow$ Validate $\rightarrow$ Implement $\rightarrow$ Verify $\rightarrow$ Promote**), the SAGE engineering node will **STOP** and await explicit manual approval before any execution code is introduced.

---

## 1. Capability to Implement

We propose implementing **Read-Only Task-to-Decision Causal Binding (`TaskDecisionBinder`)**.

### 1.1 Core Functions
1. **Chronological Monotonicity Check:** Verify that each decision's timestamp ($T_{decision}$) is greater than or equal to its parent task's creation timestamp ($T_{task}$), applying a 5-second maximum leeway buffer ($\delta_{drift}$) to account for cloud host clock drift:
   $$T_{decision} \ge T_{task} - 5\text{ seconds}$$
2. **Identifier Prefix Formatting Verification:** Ensure all input decision identifiers start with either `decision_` or `proposal_`, throwing explicit validation exceptions on violations.
3. **Duplicate Identification Check:** Enforce uniqueness constraints to reject payloads containing duplicate decision identifiers.
4. **Causal Evidence Verification:** Scan listed evidence paths in the decision to verify they refer to valid context components.

---

## 2. Dependency Justification

This capability is the correct next dependency following the successful implementation of the `SessionStateTaskLinker`:

* **Logical Progression:** The `SessionStateTaskLinker` maps and validates the session-to-task boundary (the "What" and the "Who"). The `TaskDecisionBinder` completes the lineage tree by mapping the task-to-decision boundary (the "Why" and the "How").
* **Continuous Evidence Chain:** Together, these two components construct a fully verifiable causal tree mapping a high-level cognitive objective down to its tactical task executions, and finally to its technical design decisions.
* **Prerequisite for Signing:** Complete causal lineage validation is a strict mathematical prerequisite before Milestone 2B's cryptographic signatures and nonces can be generated.

---

## 3. Exact Files Expected to Change

To ensure absolute isolation, the implementation footprint is strictly bounded:

* **`sage/experimental/act/contracts.py` (Modify):** Expand the shell `TaskDecisionBinder` class to implement the read-only chronological, format, and duplication checks.
* **`sage/experimental/act/__init__.py` (Verify):** Ensure `TaskDecisionBinder` remains correctly exported.
* **`tests/experimental/test_act_lineage_mapping.py` (Modify):** Add extensive, dedicated unit tests verifying the binder's error conditions and successful paths.

---

## 4. Expected Tests to Add/Update

We will deliver 5 dedicated validation tests inside `tests/experimental/test_act_lineage_mapping.py`:

1. `test_task_decision_causal_binder_success`: Verifies correct mapping on chronologically valid, uniquely formatted decision payloads.
2. `test_task_decision_causal_binder_chronological_violation`: Confirms rejection (raising `ValueError`) when a decision timestamp is strictly earlier than task creation.
3. `test_task_decision_causal_binder_malformed_id`: Confirms rejection when a decision identifier lacks the `decision_` or `proposal_` prefix.
4. `test_task_decision_causal_binder_duplicate_id`: Confirms rejection when duplicate decision identifiers are supplied in the same payload.
5. `test_task_decision_causal_binder_drift_tolerance`: Verifies that decisions occurring within 5 seconds prior to task creation (due to system clock drift) are successfully accepted.

---

## 5. Evidence Artifact to Produce

Upon successful local verification of the implementation slice, the active thread will generate:
* **`docs/SAGE-ACT-MILESTONE-2A-EXTENSION-IMPLEMENTATION-RECEIPT.md`**: Detailing the added source code, exact code-coverage percentage, and a record of the passing test suite execution.

---

## 6. Rollback Strategy

If any test failures, performance regressions, circular import warnings, or namespace drift issues arise during active coding:
* **Action:** Revert the workspace immediately to baseline HEAD commit `95a0027d0c0780c4b74e96cffbeb36fbb6e13f40` by running:
  ```bash
  git reset --hard 95a0027d0c0780c4b74e96cffbeb36fbb6e13f40
  ```
  This guarantees a 100% clean recovery with zero risk of baseline contamination.

---

## 7. Validation Gate After Implementation

To be promoted, the compiled code must satisfy the following post-implementation validation gate:
* **165/165 Passing Tests:** The expanded Pytest suite (comprising 150 baseline, 10 Milestone 2A, and 5 Milestone 2A Extension tests) must pass with 100% success.
* **Zero Production Footprint:** Static AST checkers must verify zero import leakage from the experimental namespace into core production directories.

---

## 8. Conclusion and STOP Signal

This proposal outlines a highly disciplined, risk-mitigated advancement path.

In absolute compliance with the authorized workflow, **the SAGE engineering node has STOPPED and is awaiting explicit approval** to proceed with the active coding phase.
