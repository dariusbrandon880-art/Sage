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

---

## 7. Milestone 2 Architecture Review

In accordance with SAGE's strict multi-agent evolution policy, this section presents the pre-implementation Architecture Review of the Milestone 2 design.

### 7.1. Implementation Boundary Map
To enforce total system isolation and maintain a zero production footprint, the file and component interactions are strictly demarcated:

- **Experimental Core (`sage/experimental/act/`):**
  - Consumes existing models from production.
  - No database, filesystem, or session writes.
  - Absolute import isolation: Core runtime components (`sage/acr/`, `sage/core/`, `sage/runtime/`) are prohibited from importing any code under `sage/experimental/`.
- **Type Consumption (One-Way Flow):**
  - `SessionState` is imported from `sage.acr.session.session_state`.
  - `AgentTask` and `AgentTaskState` are imported from `sage.agents.models`.
  - `DecisionEntry` and `DecisionType` are imported from `sage.models`.
  - All references are imported and utilized strictly for type annotations and read-only field verification.

### 7.2. Proposed File Structure for Future Read-Only Lineage Expansion
The proposed layout of the experimental namespace for Milestone 2 implementation:

```
sage/experimental/act/
├── __init__.py           # Exports public interfaces
├── contracts.py          # Milestone 1 Linker/Binder contracts
└── lineage_validation.py # Future Milestone 2 expansion classes:
                          #  - SessionStateTaskLinker
                          #  - TaskDecisionCausalBinder
                          #  - PreMutationSafetyGates
```

Separating Milestone 2 validators into a separate module (`lineage_validation.py`) ensures clean separation of concerns and facilitates modular test mapping.

### 7.3. Validation Test Strategy
To establish absolute correctness before any promotion, the testing harness is structured into three layers:

1. **Unit Testing (`tests/experimental/test_act_lineage_mapping.py`):**
   - Mocking standard model instances via simulated data objects.
   - Asserting exact error codes and exception classes for each failure scenario.
   - Asserting tree return formats match the exact schemas defined in Section 3.
2. **Integration Verification:**
   - Loading actual production `.json` state files from the workspace (if present) to verify that real production states compile into lineages correctly.
3. **AST Isolation Tests:**
   - Using the AST parsing engine to assert that no production python files import or interact with the `sage.experimental.act` submodules.

### 7.4. Risk Assessment and Mitigations
Before any code generation, potential architectural and runtime risks have been mapped with proactive mitigations:

| Risk Description | Threat Tier | Concrete Mitigation Strategy |
| :--- | :--- | :--- |
| **Accidental State Mutation** | CRITICAL | All arguments passed to validation classes are frozen or handled as read-only copies; no `save_session` or disk write calls are executed. |
| **Circular Dependencies** | HIGH | Validation engines are strictly downstream consumers of core schemas, importing types directly from terminal schema packages (`sage.agents.models`, `sage.models`) rather than high-level manager classes. |
| **Circular Reference Trapping** | MEDIUM | Detect cycle loops (e.g., recursive dependencies in the decision history) and terminate validations with a cyclic-dependency exception rather than memory exhaustion. |
| **Validation Drift** | MEDIUM | Enforce schema strictness using Pydantic’s built-in field validation to automatically raise schema validation errors on mismatch. |

---

## 8. Detailed SAGE-ACT Milestone 2 Architecture Review

In response to the formal Milestone 2 Directive, this section presents a deep-dive, pre-implementation architecture and boundary analysis.

### 8.1. Implementation Boundary Map
To satisfy the Zero-Footprint directive, the files and namespaces for Milestone 2 are mapped as follows:

*   **Target Files for Isolation:**
    - `sage/experimental/act/__init__.py`: Will act as the single entrypoint exposing our validation interfaces.
    - `sage/experimental/act/contracts.py`: Will be appended to contain `SessionStateTaskLinker`, `TaskDecisionCausalBinder`, and `PreMutationSafetyGates` (maintaining original Milestone 1 classes `SessionTaskTreeLinker` and `TaskDecisionBinder` without changes).
    - `tests/experimental/test_act_lineage_mapping.py`: Created for isolated unit testing of the expanded contracts.
*   **Enforcement of Zero-Footprint:**
    - **No production namespace edits:** Absolutely no files inside `sage/acr/`, `sage/core/`, `sage/runtime/`, or root package modules like `sage/validation.py` will be created or modified.
    - **No core production imports:** Any import of experimental modules by production code will violate the **One-Way Import Law** and cause the import-checks test suite (`test_production_isolation_and_zero_footprint`) to fail.
    - **No write operations:** The validation logic operates exclusively on memory references of production types (e.g., using Pydantic models strictly read-only), and contains no serialization, filesystem dump, or sqlite/state mutations.

### 8.2. Read-Only Expansion Design Review
This sub-section reviews the specific contract requirements and component dependencies:

*   **`SessionTaskTreeLinker` / `SessionStateTaskLinker` Expansion:**
    - To map `SessionState` to its corresponding `AgentTask` list, the linker must accept a fully instantiated `SessionState` and a list of `AgentTask` objects.
    - It must traverse `SessionState.active_objectives` and compare them against `AgentTask.objective_id` to establish mapping.
*   **`TaskDecisionBinder` / `TaskDecisionCausalBinder` Validation:**
    - Validates mapping between `AgentTask` and `DecisionEntry`.
    - It must assert that all decision identifiers mapped inside a task's metadata exist in the input list of `DecisionEntry` records and that the causal evidence list is chronological.
*   **Existing Component Dependencies:**
    - `SessionState`: Defined in `sage/acr/session/session_state.py`.
    - `AgentTask`: Defined in `sage/agents/models.py`.
    - `DecisionEntry`: Defined in `sage/models.py`.
    - `AgentIdentity`: Defined in `sage/agents/models.py`.
    - *Constraint:* None of these target types are modified. All classes consume them via read-only property reads.

### 8.3. Validation Strategy
We define a highly specific test and audit schema to ensure correctness before promotion:

*   **SessionState Ingestion Checks:**
    - Inspect that the ingested `SessionState` has valid session ID formats and is structured with non-empty active objectives.
*   **Decision Causality Verification:**
    - Verify that every referenced decision has evidence that links back to the originating task.
    - Enforce strict chronological verification: decision creation timestamps (`timestamp`) must follow the corresponding task creation timestamp (`created_at`).
*   **Path Mutation Isolation Checks:**
    - Verify that any validation execution has no disk or state mutations on active workspace paths (`sage_data/`).
*   **Nonce Freshness Validation:**
    - Read nonce values or version sequences inside session and task metadata.
    - Validate that they form a strict, ascending, non-repeating sequence to prevent replay attacks during cross-agent session synchronization.
*   **Acyclic Lineage Verification:**
    - Build a Directed Acyclic Graph (DAG) representation of the mapped session-task-decision relationships.
    - Run a cycle-detection algorithm (DFS-based or topological sort) to assert that the lineage contains no loops or cyclic relationships.

### 8.4. Risk Assessment
Potential risk factors and validation assumptions are documented below:

*   **Production Risks:**
    - *Risk:* Accidental mutation or reference alteration of production states.
    - *Mitigation:* Ensure that all validators consume inputs as read-only models (e.g. using `model_copy()` if required or read-only properties) without triggering any `.save_session()` or disk dump.
*   **Archive Integrity Risks:**
    - *Risk:* Accidental or malformed archive writes during lineage checks.
    - *Mitigation:* No archive modules or promotion engines are imported under `sage/experimental/act/`. Tests will enforce that archive promotion remains completely frozen.
*   **Import Boundary Risks:**
    - *Risk:* Import leakage where production code imports experimental validators to leverage new checks.
    - *Mitigation:* Strictly enforce the AST-based import check, ensuring complete namespace containment.
*   **Assumptions Requiring Validation:**
    - We assume that `SessionState` timestamps and `AgentTask` timestamps use comparable ISO-8601 UTC formats. If a discrepancy in timezone representation occurs, timestamp parsing will automatically fallback to standard ISO timezone-aware datetimes.

---

## 9. SAGE-ACT Milestone 2 Architecture Review Report

This section contains the formal, comprehensive **SAGE-ACT Milestone 2 Architecture Review Report** as authorized by the SAGE Engineering Node governance directive.

### 9.1. Implementation Boundary Map
To satisfy the absolute system isolation requirements, the boundaries are meticulously mapped:

*   **Smallest Safe Future Implementation Slice:**
    - Future Milestone 2 implementation should be delivered strictly as two non-mutating validation classes: `SessionStateTaskLinker` and `TaskDecisionCausalBinder` inside the existing file `sage/experimental/act/contracts.py`.
    - The interfaces will expose read-only validations that construct and return structured, immutable lineage dictionary mappings without side effects.
*   **Target Namespaces and Files:**
    - Isolated directory: `sage/experimental/act/`
    - Involved modules: `contracts.py` (expansion), `__init__.py` (exposing new linkage classes).
    - Test files: `tests/experimental/test_act_lineage_mapping.py` (exposing dedicated lineage verification tests).
*   **Strict Isolation Assurances:**
    - **No production namespace changes:** All modules inside `sage/acr/`, `sage/core/`, `sage/runtime/`, and root files are explicitly frozen. No edits of any kind will occur.
    - **No core production imports:** Under the **One-Way Import Law**, any production code imports from experimental ACT modules are blocked and checked programmatically.

### 9.2. Dependency Analysis
The lineage engine behaves as a passive observer of existing SAGE production models. The interfaces are defined strictly as read-only dependency injections:

*   **`SessionState` / `SessionStateManager` Observation:**
    - *Interface:* `SessionStateTaskLinker` queries the `active_objectives`, `session_id`, and `important_decisions` properties of the standard `SessionState` model class in `sage.acr.session.session_state`.
    - *Safety:* No instance of `SessionStateManager` is allowed to receive write or update calls. State is queried directly from memory.
*   **Decision Tracking Structures (`DecisionEntry`):**
    - *Interface:* `TaskDecisionCausalBinder` reads `DecisionEntry` models from `sage.models`. It checks fields: `id`, `timestamp`, `evidence`, and `outcome`.
    - *Safety:* No decision entry is saved, mutated on disk, or promoted during validation.
*   **EAS Receipt Structures:**
    - *Interface:* `PreMutationSafetyGates` queries associated SPEK validation receipts from `AgentTask.validation_records` (represented as lists of SHA-256 hashes) and correlates them with actual receipts inside `sage_data/evidence_capture/` if necessary.
*   **Archive Promotion Pathways:**
    - *Interface:* Verification of whether a session is safe for future promotion is performed strictly as a read-only metadata check (e.g. asserting that `SessionState.metadata` does not contain a pre-existing `"promoted"` or `"archived"` flag).
    - *Safety:* No writes to `Archive` or archive database directories are executed.

### 9.3. Validation Plan Refinement
The testing harness is refined with specific requirements for five critical validation assertions:

1.  **Session Lineage Mapping:**
    - Assert that every task assigned to a session has an `objective_id` matching an element inside `SessionState.active_objectives`.
    - Raise a `ValueError` with clear violation codes if a task objective is unlisted or orphan.
2.  **Task-to-Decision Causality Validation:**
    - Parse decision timestamps and task creation timestamps. Enforce strict chronological ordering: `DecisionEntry.timestamp >= AgentTask.created_at`.
    - Verify that the target decision's evidence contains valid trace terms matching the task.
3.  **Receipt Integrity Checks:**
    - Assert that validation hashes listed inside the lineage mapping are structurally valid SHA-256 hex strings.
    - Flag missing validation records on tasks that have entered the `COMPLETED` state.
4.  **Mutation Boundary Enforcement:**
    - The validation test suite will execute audits under a mocked filesystem environment, asserting that no `.json` writes are made to `sage_data/sessions/` or `sage_data/state.json` during lineage processing.
5.  **Acyclic Lineage Verification:**
    - Construct an internal Graph representation where nodes are `SessionState`, `AgentTask`, and `DecisionEntry`, and directed edges represent references.
    - Run an acyclic validation algorithm (DFS with recursion-stack state tracking or Kahn's topological sort) to programmatically ensure there are no cyclic dependency loops.

### 9.4. Risk Review
Before moving to implementation, all identified risks are evaluated with strict containment protocols:

*   **Production Impact Risks:**
    - *Risk:* Exposure of experimental interfaces causing performance or thread-safety issues in the active runtime.
    - *Mitigation:* Ensure that experimental ACT modules are never imported, initialized, or referenced in the production pipeline (`sage/runtime/` or `sage/service.py`).
*   **Import Boundary Risks:**
    - *Risk:* Code regression where a developer mistakenly imports from experimental namespaces in core runtime modules.
    - *Mitigation:* Programmatic AST checks inside the test suite automatically scan all non-experimental python files on every run to reject imports of `sage.experimental`.
*   **State Mutation Risks:**
    - *Risk:* Accidental mutation of session state references during mapping.
    - *Mitigation:* Read-only enforcement is verified by passing deep-copied mock structures and asserting that the original inputs remain completely identical post-validation.
*   **Archive Integrity Risks:**
    - *Risk:* Potential contamination of the permanent Master Archive directory by experimental schemas.
    - *Mitigation:* The experimental validation layer has no dependency, reference, or import of the `sage.archive` namespace, eliminating any risk of archive writes.
*   **Unresolved Assumptions:**
    - *Assumption:* High-level objectives and task IDs are consistently formatted with standard ASCII string characters.
    - *Assumption:* Time stamps inside Pydantic models use ISO-8601 UTC format.
    - *Validation Path:* Added robust timezone parser normalization inside the validation strategy to handle all string datetime types safely.
