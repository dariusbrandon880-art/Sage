# SAGE-ACT Milestone 2A: Next Capability Plan

**Document Identifier:** SAGE-ACT-NCP-8.0
**Classification:** Strategic Capability Planning
**Status:** PROPOSED
**Author:** Jules (SAGE Architecture Review Node)
**Date:** March 2026

---

## Executive Summary

Pursuant to the SAGE-ACT Milestone 2A Next Capability Planning Directive, this document outlines the **next smallest safe capability advancement** for the Agent Continuity Tree scaffolding.

SAGE-ACT's current state is validated under strict read-only parameters, successfully mapping high-level objectives in `SessionState` to `AgentTask` listings using format, objective matching, and duplication checks.

To expand on this foundation securely, the next logical capability must map and validate the chronological and evidence linkages between `AgentTask` objects and the `DecisionEntry` choices made during execution. We define this next slice as **Milestone 2A Extension: Read-Only Task-Decision Causal Binding**.

---

## 1. Current Capability State

The SAGE-ACT experimental framework currently includes the following validated capabilities:
* **`SessionTaskTreeLinker`:**
  * Checks standard `session_` and `task_` prefix format structures.
  * Validates that all associated `AgentTask` instances map perfectly to listed objectives within `SessionState.active_objectives`.
  * Detects and blocks duplicate task identifiers passed in payload trees.
  * Operates completely inside the isolated experimental `sage/experimental/act/` namespace with zero production side effects.
* **Baseline Tests:**
  * Automated tests under `tests/experimental/` verify basic schema bounds, import laws, and isolation constraints under 100% test pass metrics.

---

## 2. Proposed Next Capability

### 2.1 Capability: Read-Only Task-Decision Causal Binder (`TaskDecisionBinder`)
The highest-value next feature is to establish a rigorous read-only mapping that binds an `AgentTask` to a list of `DecisionEntry` objects generated during its execution cycle.

### 2.2 Key Functions to Implement
1. **Chronological Sequencing Check:** Validate that any linked `DecisionEntry` has a timestamp ($T_{decision}$) that is chronologically greater than or equal to the parent `AgentTask` creation timestamp ($T_{task}$), allowing a 5-second leeway buffer ($\delta_{drift}$) for clock drift:
   $$T_{decision} \ge T_{task} - 5\text{ seconds}$$
2. **Identifier Format Matching:** Validate prefix structures on all decision identifiers:
   * Must match prefix: `decision_` or `proposal_`.
3. **Duplicate Decision Rejection:** Detect and reject mapping payloads containing duplicate decision identifiers.
4. **Evidence Validation:** Scan the decision's listed `evidence` arrays and confirm that the referenced files or session context paths are structurally valid.

---

## 3. Dependency Analysis

The proposed capability consumes existing production structures in a strictly read-only fashion:

* **`DecisionEntry` model:** Retrieved from `sage/models.py`.
* **`AgentTask` model:** Retrieved from `sage/agents/models.py`.
* **Standard Datetime Libraries:** Standard library `datetime` for UTC normalization and comparison.
* **No Side-Effects:** Requires no write permissions, memory managers, or background workers inside production boundaries.

---

## 4. Implementation Scope

The boundaries of the next implementation slice are rigidly locked under zero-trust guidelines:

* **Allowed Modifications:**
  * Expand `TaskDecisionBinder` inside `sage/experimental/act/contracts.py`.
  * Create unit tests inside `tests/experimental/test_act_lineage_mapping.py`.
* **Forbidden Modifications:**
  * Changing core production paths inside `sage/runtime/` or `sage/core/`.
  * Altering the Spek policy enforcement schemas.
  * Mutating live on-disk decision files or session databases.
  * Modifying `pyproject.toml` or `poetry.lock`.

---

## 5. Validation Requirements

To be accepted, any implementation of this capability must pass the following validation gates:

* **Gate 1: Format Rejection:** Raises a subclass of `ValueError` with prefix `"SAGE-ACT Contract Violation:"` if a decision ID format does not match prefix `decision_` or `proposal_`.
* **Gate 2: Chronological Rejection:** Raises an exception if a decision's timestamp is earlier than its parent task's creation timestamp.
* **Gate 3: Duplicate ID Check:** Detects and blocks duplicate decision payloads.
* **Gate 4: Isolation Enforcement:** Static AST parsing must continue to verify 100% unidirectional import isolation.

---

## 6. Evidence Requirements

Upon successful local verification of the next slice, the active session must deliver:
1. **SAGE-ACT Milestone 2A Extension Implementation Receipt:** Detailing code paths added, test coverage, and exact execution metrics.
2. **160+ Test Green-light:** Evidence that the full test suite passes with 100% integrity.

---

## 7. Risks and Mitigations

* **Clock Drift Anomaly:** Microsecond host drift can falsely trigger chronology violations.
  * *Mitigation:* Apply strict UTC timezone normalization and build a 5-second grace period into the verification function.
* **Memory Reference Sharing:** Direct reference passing can cause accidental object mutations.
  * *Mitigation:* The `TaskDecisionBinder` must perform deep copies of all input arguments before processing.

---

## 8. Recommended Next Checkpoint

```
[M2A NCP Planning] ──► [Milestone 2A Extension Coding] ──► [M2A Extension Integration Gate]
     (CURRENT)                  (NEXT STEP)                    (160+ TEST VALIDATION)
```

The review node recommends authorizing this capability slice. The next gate will initiate the coding execution under experimental boundary locks.
