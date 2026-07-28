# SAGE-ACT Milestone 4: Active Hook & Intercept Layer Proposal

**Record ID:** SAGE-ACT-M4-PROP-2026-07-28
**Classification:** Experimental Capability Proposal
**Status:** Under Review
**Target Namespace:** `sage/experimental/act/`

---

## 1. Capability Objective

The objective of this proposal is to introduce the next sequential evolutionary capability slice: **The SAGE Active Client Hook and Intercept Layer (SAGE-ACH)**.

### 1.1. Core Focus
The focus is on **designing a lightweight, non-intrusive mock developer wrapper and command interceptor** inside the experimental namespace. SAGE-ACH hooks directly into standard agent workspace actions (e.g., executing bash tools, git operations, or file mutations), automatically capturing their outputs as structured context, and logging them directly into the newly validated SAGE Continuity Control Loop (SAGE-CCL) records.

---

## 2. Enterprise Problem Addressed

During live, complex development cycles, key context is lost because:
1. **Implicit Decisions:** Developers and AI-assisted engineering agents invoke a variety of tools (e.g., file search, git commit, terminal compiles) sequentially. The rationale and sequential output behind these actions are never preserved.
2. **Post-Hoc Reporting Latency:** Traditional logging relies on "post-hoc" reporting (recording data *after* execution is finished). If a session crashes mid-command, all intermediate state transitions, logs, and evidence are lost, blocking the recovery loop.
3. **Disconnected Audit Trails:** Compliance and security auditors can see a git commit or a modified file, but they cannot reconstruct the exact series of bash commands, search results, or compiler errors that led to that change, introducing vulnerability risks.

---

## 3. Proposed Experimental Scope

SAGE-ACH proposes a lightweight, non-intrusive command execution wrapper operating under strict sandbox boundaries.

### 3.1. Lineage Mappings
This capability establishes the physical telemetry link to automatically construct:
* $$\text{Developer Action} \longrightarrow \text{Command Executed} \longrightarrow \text{Workspace State Snapshot} \longrightarrow \text{SAGE-CCL record}$$

```
  ┌───────────────────┐      ┌──────────────────┐      ┌─────────────────┐
  │ Developer command │ ───> │ ACH Command Hook │ ───> │ Execution output│
  └───────────────────┘      └──────────────────┘      └─────────────────┘
                                                                │
                                                                ▼
  ┌───────────────────┐      ┌──────────────────┐      ┌─────────────────┐
  │  Lineage archived │ <─── │   SAGE-CCL sync  │ <─── │ Context capture │
  └───────────────────┘      └──────────────────┘      └─────────────────┘
```

### 3.2. Data Interface & Structures
SAGE-ACH will leverage a structure `ActiveInterceptHookEvent` matching the Pydantic schemas in SAGE:
```python
class ActiveInterceptHookEvent(BaseModel):
    event_id: str  # Format: ACH-EVT-YYYYMMDD-UUID
    command: str   # e.g., "pytest", "git commit -m ..."
    workspace_before: Dict[str, str] # Key files and their shas before action
    workspace_after: Dict[str, str]  # Key files and their shas after action
    exit_code: int
    execution_duration: float
    output_summary: str
    linked_record_id: Optional[str] = None # Reference to a ContinuityControlRecord
```

### 3.3. Execution Workflow
1. **Command Interception:** A developer or agent runs a command through the mock execution wrapper (e.g., `sage_run <command>`).
2. **Pre-State Capture:** SAGE-ACH captures the SHAs of crucial workspace files.
3. **Execution:** The command is executed in the sandboxed shell context.
4. **Post-State Capture & Record Synthesis:** SAGE-ACH captures the command output, exit status, and post-state changes. It generates an `ActiveInterceptHookEvent`, maps it to a `ContinuityControlRecord`, and stages it locally.

---

## 4. Implementation Boundary

SAGE-ACH strictly adheres to SAGE's One-Way Import Law:
* **Allowed Namespace:** Confined strictly to `sage/experimental/act/` and `tests/experimental/`.
* **Prohibited Modifications:** No changes to `sage/runtime/`, `sage/core/`, or `sage/acr/`.
* **Zero Production Footprint:** Standard production run commands are unaffected. The capability is initialized only when explicitly executing commands within the experimental wrapper.

---

## 5. Validation Strategy

Unit and integration tests will be written inside `tests/experimental/test_active_hook.py` to verify:
1. **Command Execution Interception:** Assert that passing command strings to the wrapper correctly executes them and captures output text, duration, and exit status.
2. **Context Differential Capturing:** Verify that changes to file states (e.g., creating a file) are captured as a structured metadata dictionary in `workspace_after`.
3. **SAGE-CCL Linkage:** Assert that every captured event is successfully written as an experimental `ContinuityControlRecord` under a `PROPOSED` status.
4. **AST Import Isolation:** Ensure that no production systems import from the SAGE-ACH wrapper module.

---

## 6. Rollback Plan

To completely remove the SAGE-ACH prototype:
1. **File Deletion:** Delete `sage/experimental/act/active_hook.py` (when implemented) and its test suite `tests/experimental/test_active_hook.py`. Remove exports from `__init__.py`.
2. **Index Reversion:** Revert the corresponding entries in `Main Archive/INDEX.md` and any registration documents.
3. **Pristine State Guarantee:** Because the prototype operates solely inside the isolated experimental directory, removing these files returns SAGE to its exact pristine state with zero risk of logical residue.

---

## 7. Demonstration Value

This next step strengthens the SAGE ecosystem by:
* **Automated Evidence Generation:** Eliminates the need to manually declare what commands led to a specific milestone.
* **Causal Linkage Audit:** Connects raw terminal command chains directly to decision-trace lines and immutable ledger receipts, making the entire engineering history inspectable.
* **Enhanced Reconstruction Reliability:** Provides an exact step-by-step history of commands that can be re-played automatically to rebuild a session state after a crash.

---

## 8. Boundary Audit & Classifications

SAGE-ACH operates under strict governance:
* **No Speculative Architecture:** The capability does not modify system routers, endpoints, or persistent state databases.
* **No CMAPS Promotion:** CMAPS v1.0 remains strictly classified as an **Architecturally Stabilized Candidate Path**.
* **Governance Classifications:**
  * **SAGE-CCL:** *Implemented Experimental Prototype*
  * **SAGE-ACH:** *Experimental Capability Proposal*

### 8.1. Operational Directives
$$\text{Research} \longrightarrow \text{Validation} \longrightarrow \text{Master Archive}$$
$$\text{Authorize} \longrightarrow \text{Implement} \longrightarrow \text{Verify} \longrightarrow \text{Archive}$$
