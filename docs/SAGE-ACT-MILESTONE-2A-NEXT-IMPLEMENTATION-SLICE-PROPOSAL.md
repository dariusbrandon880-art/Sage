# SAGE-ACT Milestone 2A: Next Implementation Slice Proposal (V2)

**Document Identifier:** SAGE-ACT-ISP-11.0
**Classification:** Pre-Implementation Architectural Proposal
**Status:** PROPOSED
**Author:** Jules (SAGE Architecture Review Node)
**Date:** March 2026

---

## Executive Summary

Pursuant to the SAGE-ACT Milestone 2A Next Implementation Slice Planning Review Authorization directive, this document establishes the **V2 implementation slice proposal** for the authorized `TaskDecisionBinder` capability expansion.

Following the structured lifecycle (**Authorize $\rightarrow$ Plan $\rightarrow$ Validate $\rightarrow$ Implement $\rightarrow$ Verify $\rightarrow$ Promote**), the SAGE engineering node has **STOPPED** and is awaiting explicit supervisor authorization before writing any active implementation code.

---

## 1. Capability to Implement

We propose the direct implementation of **Read-Only Task-to-Decision Causal Binding (`TaskDecisionBinder`)** inside `sage/experimental/act/contracts.py`.

### 1.1 Targeted Functions
1. **Chronological Monotonicity Checking:** Assert that every decision's creation timestamp ($T_{decision}$) is greater than or equal to its parent task's creation timestamp ($T_{task}$), applying a 5-second leeway buffer ($\delta_{drift}$) to accommodate potential distributed host clock drift:
   $$T_{decision} \ge T_{task} - 5\text{ seconds}$$
2. **Format Verification:** Verify regex format compatibility of all decision IDs, ensuring they start with either `decision_` or `proposal_`.
3. **Uniqueness Checking:** Scan for and block any duplicate decision identifiers within the parsed payload.

---

## 2. Dependency Justification

This capability represents the next essential step in the lineage validation framework:
* **End-to-End Mapping:** `SessionStateTaskLinker` resolves high-level objective links. The `TaskDecisionBinder` maps execution-level decisions, completing the entire causal trace.
* **Milestone 2B Foundation:** A complete end-to-end lineage mapping is required before Milestone 2B's cryptographic signatures and nonces can be generated on transition states.

---

## 3. Exact Files Expected to Change

All implementation activities are isolated strictly inside the experimental namespace:
* **`sage/experimental/act/contracts.py` (Modify):** Expand the `TaskDecisionBinder.bind_task_to_decisions` method to implement formatting, chronological, and uniqueness checks.
* **`tests/experimental/test_act_lineage_mapping.py` (Modify):** Deliver 5 extensive, dedicated unit tests verifying edge cases and error bounds.

---

## 4. Required Test Addings / Updates

We will implement the following tests in `tests/experimental/test_act_lineage_mapping.py`:
1. `test_causal_binder_success`: Verifies correct validation on formatted, chronologically valid payloads.
2. `test_causal_binder_temporal_violation`: Verifies rejection of decisions occurring strictly earlier than parent task creation.
3. `test_causal_binder_malformed_id`: Verifies rejection of decision IDs without `decision_` or `proposal_` prefixes.
4. `test_causal_binder_duplicate_id`: Verifies duplicate ID detection.
5. `test_causal_binder_drift_leeway`: Confirms that decisions created within 5 seconds before task registration are correctly accepted under clock-drift allowances.

---

## 5. Validation Evidence Artifact to Produce

Upon successful local verification of the next implementation slice, the active thread will generate:
* **`docs/SAGE-ACT-MILESTONE-2A-TASK-DECISION-CAUSAL-BINDER-VERIFICATION-REPORT.md`**: Detailing added code paths, test metrics, and exact Pytest execution output.

---

## 6. Boundary Verification Approach

To guarantee absolute production isolation:
* **Static Import Checks:** Run the automated AST import checker (`test_one_way_import_isolation_enforcement` inside `test_act_interface.py`) to confirm zero import statements leak from experimental to production layers.
* **Test Isolation Run:** Execute the full test suite (`poetry run pytest`) to verify zero regressions exist on any baseline system.

---

## 7. Rollback Strategy

If any test failures, performance regressions, circular import warnings, or namespace drift issues arise during active coding:
* **Action:** Instantly revert the workspace to baseline HEAD commit `95a0027d0c0780c4b74e96cffbeb36fbb6e13f40` by running:
  ```bash
  git reset --hard 95a0027d0c0780c4b74e96cffbeb36fbb6e13f40
  ```
  This guarantees a 100% clean recovery with zero risk of baseline contamination.

---

## 8. Expected Completion Evidence

* Delivery of a 100% passing test suite (comprising 165 tests).
* Generation of `docs/SAGE-ACT-MILESTONE-2A-TASK-DECISION-CAUSAL-BINDER-VERIFICATION-REPORT.md`.

---

## 9. Risks and Mitigations

* **Distributed Clock Drift:** System hosts can exhibit minor time desynchronizations.
  * *Mitigation:* Apply UTC timezone normalization and a 5-second grace period ($\delta_{drift}$) for all temporal validations.
* **In-Memory Mutations:** Python's default pass-by-reference behavior can cause accidental in-place mutations of active structures.
  * *Mitigation:* The `TaskDecisionBinder` must perform deep copies of all input arguments before processing.

---

## 10. Conclusion and STOP Signal

This V2 proposal represents a fully planning-validated advancement path.

In absolute compliance with SAGE governance guidelines, **the SAGE engineering node has STOPPED and is awaiting explicit authorization** to proceed with the active coding phase.
