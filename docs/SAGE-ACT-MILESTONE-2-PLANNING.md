# SAGE-ACT Milestone 2: Multi-Agent Continuity Tree Lineage Expansion Planning

**Document Identifier:** SAGE-ACT-MP-2.0
**Classification:** Experimental Planning & Design Document
**Status:** PROPOSED
**Author:** Jules (SAGE Engineering Node)
**Date:** March 2026

---

## 1. Executive Summary

This planning package outlines the architecture, data structures, and validation rules proposed for **SAGE Agent Continuity Tree (SAGE-ACT) Milestone 2: Read-Only Lineage Mapping and Validation Expansion**.

In perfect alignment with SAGE's controlled evolutionary mode (**Validated Foundation → Experimental Validation → Future Promotion**), Milestone 2 expands read-only validation capabilities to map causal flows across SAGE's three primary state containers:
1. `SessionState` (High-level cognitive sessions, objectives, and decisions).
2. `AgentTask` (Task-level routing, lifecycle execution states, and audit trails).
3. `DecisionEntry` (Causal technical, process, and architectural decision rationales).

All designed capabilities are strictly read-only, non-mutating, and isolated entirely within the experimental `sage/experimental/act/` namespace. There is **zero production footprint**, **no active runtime alterations**, and **strict compliance with the One-Way Import Law**.

---

## 2. Core Focus Areas

The implementation of Milestone 2 will focus on four specific read-only capabilities:

### 2.1. SessionState → AgentTask Lineage Inspection
- **Objective:** Establish formal read-only validation that maps a high-level `SessionState` object to its associated list of `AgentTask` instances.
- **Mapping Criteria:**
  - Ensure that the high-level objectives listed in `SessionState.active_objectives` match the target `objective_id` defined inside each associated `AgentTask`.
  - Validate that all mapped task identifiers follow the structured format (`task_<unique_id>`).

### 2.2. AgentTask → DecisionEntry Causal Mapping
- **Objective:** Establish a precise causal mapping from individual `AgentTask` instances to the specific `DecisionEntry` records created during their execution.
- **Mapping Criteria:**
  - Verify that decision identifiers defined in the `AgentTask.metadata` or related references map to valid, resolvable `DecisionEntry` objects.
  - Trace the decision's listed evidence back to the task or session context to establish a continuous evidence chain.

### 2.3. Validation of Lineage Integrity and Malformed-State Rejection
- **Objective:** Guard against structural, chronological, or logic-level corruption across the mapping.
- **Rejection Rules (Mandatory):**
  - **Mismatched Objectives:** Reject mappings where a task is linked to a session but refers to an objective not listed in that session's `active_objectives`.
  - **Temporal / Chronological Violations:** Reject mappings where an associated `DecisionEntry` timestamp is strictly earlier than the associated `AgentTask` creation timestamp (`created_at`).
  - **Orphan Tasks / Decisions:** Identify and flag tasks or decisions that claim relationship to a session but are not present or indexed in the primary session list.
  - **Duplicate Mappings:** Reject trees containing duplicate task or decision identifiers.

### 2.4. Additional Read-Only Safety Checks Before Any Future Mutation Capability
- **Objective:** Validate pre-requisites and system invariants *before* future state modifications can ever be permitted.
- **Invariants Audited:**
  - **Session Finalization Invariant:** Confirm that safety checks reject any validation requests on sessions marked as finalized or archived in their metadata.
  - **Identity Authority Verification:** Verify that the assigned agents on tasks hold active, valid `AgentIdentity` structures inside `sage/agents/models.py`.
  - **Receipt Chain Coherency:** Read and verify that target validation record hashes match existing hashes to block signature or nonce replay attacks before execution.

---

## 3. Class and Method Interface Design

Milestone 2 introduces three new read-only interface structures in `sage/experimental/act/contracts.py`:

### 3.1. `SessionStateTaskLinker`
Responsible for deep inspection of `SessionState` to `AgentTask` relationships.

```python
class SessionStateTaskLinker:
    """Enforces deep read-only lineage validation mapping SessionState to AgentTasks."""

    def __init__(self, validation_mode: str = "strict"):
        self.validation_mode = validation_mode

    def validate_session_task_lineage(
        self,
        session: Any,  # Expected: SessionState
        tasks: List[Any]  # Expected: List[AgentTask]
    ) -> Dict[str, Any]:
        """Validates that all tasks belong logically to the given session.

        Raises:
            ValueError: On objective mismatch, orphan task, or duplicate task ID.
        """
        pass
```

### 3.2. `TaskDecisionCausalBinder`
Responsible for validating the causal link between `AgentTask` and `DecisionEntry`.

```python
class TaskDecisionCausalBinder:
    """Enforces chronological and evidence alignment between AgentTasks and DecisionEntries."""

    def __init__(self, validation_mode: str = "strict"):
        self.validation_mode = validation_mode

    def validate_causal_mapping(
        self,
        task: Any,  # Expected: AgentTask
        decisions: List[Any]  # Expected: List[DecisionEntry]
    ) -> Dict[str, Any]:
        """Validates chronological ordering and evidence linkages.

        Raises:
            ValueError: On chronological violation, unresolvable evidence, or duplicate ID.
        """
        pass
```

### 3.3. `PreMutationSafetyGates`
Runs safety checks on the complete mapped tree before any prospective future mutation is authorized.

```python
class PreMutationSafetyGates:
    """Read-only check suite that blocks state mutations if invariants are violated."""

    def __init__(self):
        pass

    def enforce_pre_mutation_checks(
        self,
        session_id: str,
        lineage_tree: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Executes all read-only invariant audits.

        Returns:
            A status dictionary detailing safety verification.
        """
        pass
```

---

## 4. File Impact Report

| File Path | Type | Action | Description / Purpose |
| :--- | :--- | :--- | :--- |
| `sage/experimental/act/contracts.py` | Python Code | Overwrite / Append | Add Milestone 2 read-only validator classes and methods without changing the existing Milestone 1 contract classes. |
| `tests/experimental/test_act_lineage_mapping.py` | Python Test | Create | Add rigorous test cases validating standard mapping, malformed state rejection, and safety invariant audits. |
| `docs/SAGE-ACT-MILESTONE-2-PLANNING.md` | Markdown Spec | Create | This formal design and planning specification file. |
| `Main Archive/INDEX.md` | Markdown Index | Append | Register this planning document under `PROPOSED` state. |

---

## 5. Validation and Test Strategy

### 5.1. Unit Testing
Using simulated objects of `SessionState`, `AgentTask`, and `DecisionEntry`, we will test:
- **Positive Paths:** Correct mapping returns structured lineage metadata with `validation_status: "LINEAGE_VALIDATED"`.
- **Negative Paths:**
  - Objective mismatch (reject with explicit error message).
  - Temporal inconsistency (decision timestamp earlier than task creation; reject with chronological error).
  - Duplicated IDs in input payload (reject duplicate elements).
  - Malformed formats (invalid prefixes for task/session/decision).

### 5.2. Integration Verification
Verify that:
- Core production structures are successfully consumed as arguments without modifying them on-disk.
- Mapped trees represent exact structural states from `sage_data/`.

### 5.3. One-Way Import Law Guard
The existing import checking tests (`tests/experimental/test_act_interface.py`) will automatically verify that no files in the production directories import from `sage/experimental/`.

---

## 6. Compatibility & Production Footprint Confirmation

- **Zero Production Footprint:** All code additions are restricted to `sage/experimental/act/` and `tests/experimental/`.
- **Zero Configuration Drift:** No additions to dependencies in `pyproject.toml` or changes to `render.yaml`.
- **Backward Compatibility:** All existing 157 tests continue to pass 100% cleanly.
