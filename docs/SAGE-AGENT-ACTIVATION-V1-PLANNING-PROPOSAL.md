# SAGE Agent Activation v1 Planning Proposal

**Document Identifier:** SAGE-ACT-AAP-12.0
**Classification:** Pre-Implementation Architectural Proposal
**Status:** PROPOSED
**Author:** Jules (SAGE Architecture Review Node)
**Date:** March 2026

---

## Executive Summary

Pursuant to the SAGE SAGE-ACT Agent Activation v1 Planning Authorization directive, this document establishes the **formal planning proposal** to transition SAGE from validated read-only continuity scaffolding into governed agent operation.

By reviewing existing SAGE-ACT structures, ACR continuity foundations, and agent workflows, we define the **smallest safe capability slice** for SAGE Agent Activation v1.

In perfect alignment with SAGE's progressive lifecycle (**Authorize $\rightarrow$ Plan $\rightarrow$ Validate $\rightarrow$ Implement $\rightarrow$ Verify $\rightarrow$ Promote**), the SAGE engineering node has **STOPPED** and is awaiting explicit supervisor authorization before writing any active implementation code.

---

## 1. Current Validated State Review

The SAGE repository maintains an immaculate baseline state:
* **Production Protection:** All directories inside `sage/acr/`, `sage/core/`, and `sage/runtime/` remain completely untouched.
* **SAGE-ACT Read-Only Foundations:**
  * `SessionStateTaskLinker`: Fully validates Session-to-Task ID formatting, objective alignment strings, and rejects duplicates.
  * `TaskDecisionBinder` (M2A Proposal): Defines Task-to-Decision causal binding, format verification, and chronological monotonicity checks.
* **Test Status:** 100% PASS (all 160 baseline and experimental tests pass with zero warnings).

---

## 2. Proposed Next Capability

### 2.1 Capability to Implement: Governed Simulation Mode Agent Worker (`GovernedAgentSimWorker`)
We propose introducing a **Governed Simulation-Only Agent Worker** within the experimental namespace.

### 2.2 Core Functions
1. **Simulation-Only Dispatch:** Spawns a mock agent execution thread that parses local context files without making any changes to production systems or the active `ControlPlane` database.
2. **Dynamic Permission Check:** Prior to execution, queries the agent's `PermissionBoundary` (from `sage/agents/models.py`) to statically check whether the assigned directories or actions are within allowed boundaries.
3. **Causal Evidence Generation:** Logs simulated events, outputs structured decision recommendations, and automatically structures them into a mock `TaskEvent` schema.

---

## 3. Dependency Analysis

This capability represents the logical transition from passive lineage logging to active agent operation:
* **Existing Foundations:** It consumes the `AgentIdentity` and `PermissionBoundary` schemas already defined in the baseline (`sage/agents/models.py`).
* **Lineage Chain Bind:** It connects to the newly established read-only lineage checks (`SessionStateTaskLinker` and `TaskDecisionBinder`) to ensure that simulated steps are Causally Monotonic before dispatch.
* **Bridge to Milestone 3:** Delivering a simulation-only agent runner is the final, essential milestone before SAGE can execute actual state mutations on the active database.

---

## 4. Expected Files Affected

The implementation scope is strictly locked to prevent protected layer contamination:
* **`sage/experimental/act/agent_runner.py` (Create):** Define the `GovernedAgentSimWorker` and simulation dispatch methods under experimental isolation.
* **`sage/experimental/act/__init__.py` (Modify):** Export the new `GovernedAgentSimWorker` class.
* **`tests/experimental/test_agent_activation_v1.py` (Create):** Add rigorous unit tests to verify the simulation worker bounds.

---

## 5. Required Tests

We will deliver 5 extensive unit tests to guarantee robustness:
1. `test_sim_worker_permission_boundary_success`: Verifies correct simulated execution when files and actions lie perfectly within the agent's `PermissionBoundary`.
2. `test_sim_worker_permission_boundary_violation`: Confirms that the runner throws a subclass of `ValueError` (with the mandatory prefix `"SAGE-ACT Contract Violation:"`) if the agent attempts an action on a prohibited path.
3. `test_sim_worker_causal_monotonicity_enforcement`: Confirms that simulated actions must strictly follow chronological monotonicity check rules.
4. `test_sim_worker_identity_verification`: Rejects simulation runs where the assigned agent ID does not have a matching valid `AgentIdentity` registered.
5. `test_sim_worker_read_only_isolation`: Verifies that the simulated agent run creates zero file mutations inside the active system folders.

---

## 6. Evidence Artifact

Upon successful local verification of SAGE Agent Activation v1, the active thread will deliver:
* **`docs/SAGE-AGENT-ACTIVATION-V1-IMPLEMENTATION-RECEIPT.md`**: Detailing class structures created, simulated execution metrics, and a full green-light run of the test suite.

---

## 7. Boundary Verification

* **Static Import Checks:** Our existing AST validator checks ensure that zero import paths from production directories map to `sage/experimental/`.
* **Zero Production Footprint:** All simulated actions must write exclusively to in-memory mocks, leaving all on-disk JSON databases unchanged.

---

## 8. Rollback Strategy

If any test failures, performance regressions, circular import warnings, or namespace drift issues arise during active coding:
* **Action:** Revert the workspace immediately to baseline HEAD commit `95a0027d0c0780c4b74e96cffbeb36fbb6e13f40` by running:
  ```bash
  git reset --hard 95a0027d0c0780c4b74e96cffbeb36fbb6e13f40
  ```
  This guarantees a 100% clean recovery with zero risk of baseline contamination.

---

## 9. Risks and Mitigations

* **Scope Contamination Risk:** A developer might accidentally import a production worker class within the simulated worker.
  * *Mitigation:* Enforce absolute modular decoupling. The `GovernedAgentSimWorker` must rely exclusively on in-memory dictionary-based mock models, avoiding any direct linkage to production workers.
* **Reference Modification Risk:** Simulated agents might modify passed production objects.
  * *Mitigation:* Perform immediate deep-copies of all parameters upon receiving them in the experimental activation layer.

---

## 10. Conclusion and STOP Signal

This proposal defines a safe, progressive capability block that matures SAGE agent workflows under absolute isolation.

In strict compliance with the established governance guidelines, **the SAGE engineering node has STOPPED and is awaiting explicit planning review authorization** before writing any active implementation code.
