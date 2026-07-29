# SAGE SDR Experiment Registry and Control Framework

This document outlines the architectural specifications, schemas, lifecycles, and governance rules for the **SAGE Safe Dry-Run (SDR) Experiment Registry and Control Framework**. It establishes the formal governance container required to manage and monitor future SAGE multi-agent simulations safely.

This is a research and validation design specification. It does **not** introduce any production agent systems, autonomous workflows, or runtime coordination services. It strictly respects all core protected directories (`sage/runtime/`, `sage/core/`, `sage/acr/`).

---

## Section 1 — Purpose

The core purpose of the SAGE SDR Experiment Registry and Control Framework is to:
1. **Prevent Unregulated Experimentation:** Ensure no multi-agent simulation is run within the SAGE ecosystem without formal pre-registration and boundary reviews.
2. **Link Experiments and Governance:** Align SDR simulations with SAGE's parallel validation and evidence lifecycle frameworks, converting execution traces directly into immutable governance evidence.
3. **Isolate Sandbox Execution from Core Production:** Maintain a strict physical and logical barrier between simulation execution and the live capability promotion flow. Simulating a capability must not automatically promote it to core without explicit human reviewer signoff.

---

## Section 2 — Experiment Registry Model

Every proposed SAGE SDR experiment must be registered under a structured schema containing exactly twelve required fields:

| Field Name | Expected Type | Format & Constraint | Description |
| :--- | :--- | :--- | :--- |
| **`experiment_id`** | `str` | Must match pattern `^sdr_exp_[a-zA-Z0-9_]{3,64}$` | Unique identifier for the simulation run. |
| **`experiment_name`** | `str` | Non-empty string | Human-readable name of the experiment. |
| **`research_objective`** | `str` | Non-empty string | Clear statement of what the experiment aims to validate. |
| **`responsible_coordinator`**| `str` | Non-empty string | The authorized SAGE operator/supervisor managing this run. |
| **`participating_agents`** | `list[str]` | List of valid agent IDs (e.g., `agent_jules`, `agent_claude`) | The specific AI agent nodes involved in the simulation. |
| **`simulation_boundary`** | `str` | Non-empty string; must specify experimental paths | Approved, isolated directory path where the simulation runs. |
| **`protected_systems_excluded`**| `list[str]` | Must list `sage/runtime/`, `sage/core/`, `sage/acr/` | Explicit confirmation of directories strictly protected from mutation. |
| **`expected_evidence_output`**| `str` | Point to a target file in `evidence_capture/` | File path where the resulting execution trace and logs are stored. |
| **`validation_criteria`** | `list[str]` | List of non-empty strings | Specific programmatic metrics and rules required to pass. |
| **`reviewer_identity`** | `str` | Non-empty string | Assigned SAGE reviewer role responsible for human signoff. |
| **`archive_destination`** | `str` | E.g. `Main Archive/sdr_exp_..._archive.json` | Designate storage path inside the immutable archive tree. |
| **`lifecycle_state`** | `str` | One of: `proposed`, `approved`, `active`, `archived` | Active status of the experiment. |

---

## Section 3 — Experiment Lifecycle

SAGE SDR experiments proceed sequentially through exactly eight governance states:

1. **Research Proposal:** The authorized coordinator drafts the experimental intent and registers the research objective.
2. **Registry Entry Creation:** A structured, pending-review entry is added to the SAGE SDR Experiment Registry with `lifecycle_state="proposed"`.
3. **Boundary Review:** Automated/adversarial audits verify that the `simulation_boundary` is strictly isolated and that all protected core directories are listed under `protected_systems_excluded`.
4. **Human Authorization:** SAGE human supervisor reviews the proposal and signs off, transitioning the state to `approved` and authorizing execution.
5. **Controlled SDR Execution:** The dry-run simulation is triggered inside the isolated sandbox space, transitioning state to `active`.
6. **Evidence Collection:** Detailed traces, logs, and outputs are programmatically written to the expected evidence capture directory.
7. **Independent Review:** An independent auditor (such as Claude) reviews the collected evidence against validation criteria and the supervisor compiles a Human Review Gate audit trace.
8. **Archive Decision:** Upon successful signoff, the registry entry and its associated evidence receipts are securely moved to the designate archive destination, transitioning state to `archived`.

---

## Section 4 — Experiment Evidence Model

To satisfy SAGE’s Evidence Lifecycle framework, every completed SDR experiment must compile exactly ten required evidence artifacts:

1. **`experiment_description` (`str`):** Detailed narrative of the simulated task and scenario.
2. **`inputs` (`dict`):** The configuration parameters, workspace snapshots, and prompts fed to the participating agents.
3. **`outputs` (`dict`):** Code files, markdown specifications, or traces generated during the simulation.
4. **`agent_participation_record` (`list[dict]`):** Specific trace of each agent’s contributions, actions, and role boundaries.
5. **`timestamps` (`dict`):** Chronological records of execution start, handoffs, and completion times.
6. **`logs` (`list[str]`):** Complete standard outputs and debugging logs recorded during execution.
7. **`validation_results` (`dict`):** Output from the programmatic validators showing compliance with validation criteria.
8. **`failure_records` (`list[dict]`):** Specific exceptions, boundary alerts, or error traces intercepted during the run.
9. **`review_conclusion` (`dict`):** Final signoff notes, reviewer identity, and approved/rejected status from the Human Review Gate.
10. **`archive_reference` (`str`):** Designated file path where this completed evidence package is archived in the Master Archive.

---

## Section 5 — Experiment Failure Handling

To maintain repository-side referential integrity, SDR simulations must handle anomalous execution states deterministically:

- **Failed Experiments:** Runs that crash, raise unhandled exceptions, or fail to meet the validation criteria are flagged as `failed` in the registry. No associated code may be promoted, but the complete trace is preserved for research post-mortems.
- **Incomplete Evidence:** If an experiment finishes execution but fails to compile all ten required evidence artifacts, the registry entry remains locked in `active` state and is blocked from archival.
- **Boundary Violations:** Any attempt by a simulated agent to write or mutate files within `protected_systems_excluded` (such as `sage/runtime/`) must immediately trigger a SAGE SPEK violation, abort execution, roll back the workspace to its pre-simulation snapshot, and flag the registry entry as `aborted`.
- **Invalid / Duplicate / Abandoned Paths:**
  - *Invalid results* are immediately purged from promotion consideration.
  - *Duplicate experiments* with matching registry IDs are blocked on intake.
  - *Abandoned research paths* must be updated in the registry with a formal supervisor note detailing why the path was discarded.

---

## Section 6 — Registry Governance Rules

The SAGE SDR Experiment Registry is enforced by four absolute governance laws:

$$\begin{aligned}
\text{No Registry Entry} &\implies \text{No Experiment Execution} \\
\text{No Evidence Output} &\implies \text{No Programmatic Validation} \\
\text{No Review Gate Signoff} &\implies \text{No Archive Movement} \\
\text{No Human Approval} &\implies \text{No Live SDR Execution}
\end{aligned}$$

---

## Section 7 — Future SDR Expansion Requirements

The following six prerequisites must be programmatically verified and approved before SAGE can transition from research assessment into any active, live dry-run simulations:
1. **Approved Registry System:** An automated, file-based registry database (e.g. `sdr_registry.json`) is initialized under experimental boundaries.
2. **Validated Evidence Schema:** Structured JSON/Pydantic schemas matching the 10 required evidence artifacts are registered.
3. **Assigned Reviewers:** Explicit developer and supervisor roles are assigned and authenticated via SAGE API keys.
4. **Rollback Procedures:** Fast, automatic workspace rollbacks are validated using SAGE's workspace snap-shotting capabilities.
5. **Boundary Verification:** Strict SPEK and import path checkers are running during execution to block protected directory mutations.
6. **Human Authorization:** An active human-in-the-loop dashboard is implemented to review and approve proposed registry proposals.
