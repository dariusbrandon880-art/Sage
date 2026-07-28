# SAGE-ACT Milestone 4: Active Hook & Intercept Layer Refined Proposal

**Record ID:** SAGE-ACT-M4-PROP-2026-07-28
**Classification:** Experimental Capability Proposal
**Status:** Under Review (Scope Refined)
**Target Namespace:** `sage/experimental/act/`

---

## 1. Capability Objective

The objective of this proposal is to introduce the next sequential evolutionary capability slice: **The SAGE Active Client Hook and Intercept Layer (SAGE-ACH)**.

### 1.1. Core Focus
The focus is on **designing a lightweight, non-intrusive mock developer command execution hook** inside the experimental namespace. SAGE-ACH hooks directly into standard agent workspace actions (e.g., executing test commands, linting, or file reads), automatically capturing their execution summaries as structured context, and logging them directly into the newly validated SAGE Continuity Control Loop (SAGE-CCL) records.

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

---

## 4. Refined Technical Specifications

### 4.1. Exact Capability Boundary
SAGE-ACH operates strictly inside `sage/experimental/act/` and has **zero** authority to alter, schedule, or block execution streams of any command. It functions strictly as an **observational hook**—wrapping command execution to read metadata and outputs without controlling or automating active state transitions.

### 4.2. Inputs
SAGE-ACH receives the following inputs:
* `command`: The string command target to wrap (e.g., `"poetry run pytest tests/experimental/"`).
* `session_id`: The active session identifier format `^session_[a-fA-F0-9]{8}$`.
* `target_files`: List of filepaths in the workspace to monitor for SHA shifts (default: `["Main Archive/INDEX.md", "pyproject.toml"]`).

### 4.3. Outputs
SAGE-ACH outputs:
* `ActiveInterceptHookEvent`: An in-memory, machine-validatable instance mapping the execution metadata.
* `SAGE-CCL Record`: An automatically generated, staged `ContinuityControlRecord` synchronized to `sage_data/experimental_ccl/` under a `PROPOSED` state.

### 4.4. Captured Evidence Fields
To ensure high-fidelity lineage and accountability, SAGE-ACH captures and preserves:
* `event_id`: Unique trace identifier format `^ACH-EVT-[0-9]{8}-[a-fA-F0-9\-]{36}$`.
* `timestamp`: Epoch start and stop timestamps.
* `exit_code`: Execution status code of the wrapped process (e.g., `0` for success).
* `execution_duration`: CPU and wall time elapsed.
* `workspace_state_before`: File-to-SHA-256 mapping of observed files *before* execution.
* `workspace_state_after`: File-to-SHA-256 mapping of observed files *after* execution.
* `output_summary`: Captures stdout/stderr summary blocks (truncated to 1000 characters to prevent buffer bloat).
* `governance_checksum`: SHA-256 checksum of the intercepted metadata ensuring un-tampered record lineage.

---

## 5. Human Approval & Governance Boundaries

* **Observation Over Control:** SAGE-ACH cannot intercept standard shell commands unless explicitly wrapped via `sage_run`. It does not execute commands automatically, and holds no scheduling or process management authority.
* **Evidence Capture Over Automation:** The loop's role is solely to gather metadata. It does not auto-commit, auto-push, or auto-apply code fixes.
* **Read-Only Behavior:** Command wrappers only read state (e.g., executing `git diff` or reading file hashes). They do not mutate core files or alter system structures.
* **Approval Gate:** All newly generated `SAGE-CCL` records are staged with `lifecycle_state = "PROPOSED"`. Promotion to `VALIDATED` remains strictly locked behind manual human-operator signature verification (`sig_...`).

---

## 6. Implementation Boundary & Security

* **Target Namespace:** Confined strictly to `sage/experimental/act/active_hook.py` and `tests/experimental/test_active_hook.py`.
* **One-Way Import Law:** Experimental code may import model schemas from `sage.acr.session` or `sage.experimental.act.continuity_control`, but production modules (`sage/runtime/`, `sage/core/`, `sage/acr/`) must **never** import from experimental active hook files.
* **Security & Sandboxing:** Process spawning is strictly restricted to standard subprocess parameters without shell exposure (`shell=False`) wherever possible, mitigating potential prompt injection command-escalation vulnerabilities in wrapped environments.

---

## 7. Validation Strategy

The SAGE-ACH prototype will be validated through dedicated tests in `tests/experimental/test_active_hook.py` asserting:
1. **Mock Execution Interception:** Verifies that commands like `echo "test"` correctly capture outputs, exit codes, and durations.
2. **State Shift Tracking:** Tests assert that file modifications are successfully detected by comparing `workspace_state_before` and `workspace_state_after` hashes.
3. **Causal Linkage Validation:** Checks that executing a command automatically generates a corresponding `ContinuityControlRecord` staged inside the CCL directory.
4. **Pristine core isolation:** Automated AST import parser checks ensure zero production coupling.

---

## 8. Rollback Plan

Should the SAGE-ACH experiment need to be removed or reverted:
1. **File Deletion:** Delete `sage/experimental/act/active_hook.py` (when implemented) and its test suite `tests/experimental/test_active_hook.py`. Remove exports from `__init__.py`.
2. **Index Reversion:** Revert the corresponding entries in `Main Archive/INDEX.md` and any registration documents.
3. **Pristine State Guarantee:** Because the prototype operates solely inside the isolated experimental directory, removing these files returns SAGE to its exact pristine state with zero risk of logical residue.

---

## 9. Demonstration Value

This next step strengthens SAGE's core value proposition:
* **Automated Trace Gathering:** Saves human operators from manual status logging between sessions.
* **Better Audit Readiness:** Demonstrates end-to-end evidence tracking that is easily inspectable by human auditors.
* **Clearer Decision History:** Connects actions directly to their underlying justifications, eliminating ambiguity around why specific code changes were introduced.

---

## 10. Boundary Audit & Classifications

* **CMAPS v1.0:** *Architecturally Stabilized Candidate Path*
* **Continuity Control Loop (SAGE-CCL):** *Implemented Experimental Prototype*
* **Active Hook and Intercept Layer (SAGE-ACH):** *Experimental Capability Proposal*

### 10.1. Operational Directives
$$\text{Research} \longrightarrow \text{Validation} \longrightarrow \text{Master Archive}$$
$$\text{Authorize} \longrightarrow \text{Implement} \longrightarrow \text{Verify} \longrightarrow \text{Archive}$$
