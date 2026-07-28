# SAGE Agent Activation v1 Transition Plan

**Document Identifier:** SAGE-ACT-ATP-13.0
**Classification:** Strategic Transition Planning
**Status:** PROPOSED
**Author:** Jules (SAGE Architecture Review Node)
**Date:** March 2026

---

## Executive Summary

Pursuant to the SAGE Agent Activation v1 Transition Planning Directive, this document establishes the **formal transition plan** to move SAGE safely from validated, read-only lineage-mapping infrastructure into controlled, simulated agent operation.

By auditing existing SAGE-ACT experimental contracts, task lineages, causal evidence binders, and agent schemas, we define the **smallest safe transition capability slice** for SAGE Agent Activation v1.

Consistent with SAGE's progressive lifecycle (**Authorize $\rightarrow$ Plan $\rightarrow$ Validate $\rightarrow$ Implement $\rightarrow$ Verify $\rightarrow$ Promote**), the SAGE engineering node has **STOPPED** and is awaiting explicit supervisor authorization before writing any active implementation code.

---

## 1. Current Validated Baseline

We audited the active baseline of the repository:

* **Current Baseline Commit SHA:** `95a0027d0c0780c4b74e96cffbeb36fbb6e13f40` (validated main HEAD commit).
* **Existing SAGE-ACT Foundations:**
  * `SessionStateTaskLinker` inside `sage/experimental/act/contracts.py` (lineage validation slice completed).
  * `TaskDecisionCausalBinder` inside `sage/experimental/act/contracts.py` (completed and verified causal binding slice).
* **Production Baseline Status:** Pristine, isolated, and unchanged. Active production folders (`sage/acr/`, `sage/core/`, `sage/runtime/`) remain 100% clean.
* **Test Status:** 100% PASS (all 160 baseline and experimental tests pass cleanly in the workspace with zero failures).

---

## 2. Evidence Reviewed

The validation node conducted a formal review of the following completed SAGE-ACT Milestone 2A evidence artifacts:

1. **SessionStateTaskLinker Implementation:** Verifies task ID formats, active objectives, and duplicate rejections.
2. **TaskDecisionCausalBinder Implementation:** Verifies chronological consistency, decision prefixes, and duplication rejection.
3. **Continuity Progression Review (`docs/SAGE-ACT-MILESTONE-2A-CONTINUITY-PROGRESSION-REVIEW.md`):** Certifies orderly advancement and zero duplicate artifact generation.
4. **SAGE Agent Activation v1 Planning Proposal (`docs/SAGE-AGENT-ACTIVATION-V1-PLANNING-PROPOSAL.md`):** Outlines the initial conceptual framework for simulated agent runs.

---

## 3. Capability to Introduce

### 3.1 Proposed Capability: Governed Simulation Agent Worker (`GovernedAgentSimWorker`)
We propose introducing a **Governed Simulation-Only Agent Worker** within SAGE's experimental folder.

### 3.2 Key Features
1. **In-Memory Context Simulation:** Spawns mock agent execution workflows utilizing deep-copied contexts, ensuring zero write calls are executed on the host filesystem or active databases.
2. **Static Permission Boundary Checking:** Intercepts agent action requests and statically compares them against the agent's assigned `PermissionBoundary` (from `sage/agents/models.py`) prior to dispatching simulated workflows.
3. **Trace Generation:** Formulates simulated outputs directly into standard `TaskEvent` structures for chronological audit tracking.

---

## 4. Dependency Reasoning

This capability is the logical transition block after lineage validation:
* **Current Validated State:** SAGE-ACT successfully validates task-to-session and decision-to-task causal mappings.
* ** логический Link:** The simulation worker binds these read-only lineage checks together. It runs actual agent identities through a mock execution loop *after* lineage mappings are statically verified.
* **Controlled Progression:** A simulation-only runner acts as the final sandbox check, proving that permission boundaries are dynamically enforceable before active, database-mutating execution is authorized in Milestone 3.

---

## 5. Expected Files

To preserve absolute baseline protection, all changes are isolated to experimental zones:
* **`sage/experimental/act/agent_runner.py` (Create):** Define the `GovernedAgentSimWorker` class and simulation loop.
* **`sage/experimental/act/__init__.py` (Modify):** Export `GovernedAgentSimWorker`.
* **`tests/experimental/test_agent_sim_worker.py` (Create):** Deliver comprehensive, isolated verification tests.

---

## 6. Required Tests

We will deliver 5 dedicated unit tests inside `tests/experimental/test_agent_sim_worker.py`:
1. `test_agent_sim_worker_boundary_compliance`: Verifies correct simulated dispatch when files and actions lie perfectly within allowed paths.
2. `test_agent_sim_worker_boundary_violation`: Confirms that attempts to read/write on prohibited paths raise a subclass of `ValueError` (prefixed with `"SAGE-ACT Contract Violation:"`).
3. `test_agent_sim_worker_invalid_identity`: Rejects runs referencing unregistered or unsigned agent identities.
4. `test_agent_sim_worker_causal_monotonicity`: Confirms simulated steps are chronologically monotonic.
5. `test_agent_sim_worker_read_only_invariance`: Statically asserts that the worker makes zero disk writes or database calls.

---

## 7. Evidence Artifact

Upon successful validation of the transition slice, the active thread will deliver:
* **`docs/SAGE-AGENT-ACTIVATION-V1-TRANSITION-RECEIPT.md`**: Detailing class parameters, testing logs, and a full green-light execution trace under absolute isolation.

---

## 8. Boundary Protection

* **Circular Import Block:** Automated AST import parsers confirm zero import leakage from `sage.experimental.act` into production.
* **Write Boundary Protection:** The worker executes purely in-memory, leaving all on-disk JSON databases unchanged.

---

## 9. Rollback Strategy

If any test failures, performance regressions, circular import warnings, or namespace drift issues arise during active coding:
* **Action:** Instantly revert the workspace to baseline HEAD commit `95a0027d0c0780c4b74e96cffbeb36fbb6e13f40` by running:
  ```bash
  git reset --hard 95a0027d0c0780c4b74e96cffbeb36fbb6e13f40
  ```
  This guarantees a 100% clean recovery with zero risk of baseline contamination.

---

## 10. Risks and Mitigations

* **Implicit Mutability Risk:** Python's pass-by-reference nature can cause accidental mutation of live production models passed to the simulator.
  * *Mitigation:* Force deep-copying on all input parameters upon entering the `GovernedAgentSimWorker` execution boundary.
* **Distributed Clock Drift Risk:** System hosts can exhibit minor time offsets.
  * *Mitigation:* Apply UTC timezone normalization and a 5-second grace period ($\delta_{drift}$) for all temporal checks.

---

## 11. Recommended Next Checkpoint

```
[Agent Act v1 Plan] ──► [Agent Sim Worker Coding] ──► [Agent Sim Integration Gate]
     (CURRENT)                 (SESSION 1)                   (160+ TEST VALIDATION)
```

The review node recommends authorizing this transition capability. In absolute compliance with SAGE guidelines, **the SAGE engineering node has STOPPED and is awaiting explicit authorization** before writing any active implementation code.
