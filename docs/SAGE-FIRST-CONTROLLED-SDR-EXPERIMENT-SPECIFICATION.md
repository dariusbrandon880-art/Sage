# SAGE First Controlled SDR Experiment Specification

This document presents the definitive experimental design specification for SAGE's first controlled **Safe Dry-Run (SDR) Simulation**. It outlines the precise purpose, scope, registry attributes, validation rules, evidence requirements, and human checkpoints to validate SAGE's complete governance lifecycle in a safe, sandboxed, and isolated environment.

This is an experimental design specification and does **not** execute any production code mutations. Core protected boundaries (`sage/runtime/`, `sage/core/`, `sage/acr/`) remain entirely untouched.

---

## Section 1 — Experiment Purpose

The core objective of the first SAGE SDR experiment is to **programmatically demonstrate and validate SAGE's complete 8-stage governance lifecycle** under experimental boundaries.

By running a mock multi-agent task execution within a strictly bounded sandbox, the experiment aims to prove that:
- No agent-directed task can execute without pre-registration and active human authorization.
- Active agent execution traces can be captured and compiled into structurally compliant Capability Evidence Receipts automatically.
- Programmatic validations and manual human review gates successfully control capability promotion, keeping the Master Archive synchronized and secure.

---

## Section 2 — Experiment Scope

The scope of the first simulation run is strictly limited to prevent any accidental side effects or privilege escalation:

- **Included Actions (Allowed):**
  - Initialization of a mock workspace directory under `sage/experimental/sdr/scratch/`.
  - Simulating a mock multi-agent handoff flow between `agent_chatgpt` (Strategic Coordination) and `agent_jules` (Repository Execution).
  - Programmatically parsing a mock capability passport and validating its attributes.
  - Recording simulation logs, timestamps, and validation traces into a structured JSON file.
- **Excluded Actions (Prohibited):**
  - Mutating, writing, or deleting files in any core directories.
  - Calling live, un-mocked OpenAI or Google AI APIs.
  - Automatically updating the Master Index registry (`Main Archive/INDEX.md`) without manual human operator signoff.
- **Protected Boundaries:**
  - Standard core namespaces (`sage/runtime/`, `sage/core/`, `sage/acr/`) remain strictly write-protected. SAGE SPEK logic will immediately intercept and abort any write attempts targeting these paths.
- **Success Criteria:**
  - Completion of all 8 sequential lifecycle stages with zero unhandled exceptions.
  - Verification that the generated evidence package contains all ten required artifacts.
  - Verification that the simulation environment is cleanly torn down and rolled back to its pre-simulation snapshot.

---

## Section 3 — Experiment Registry Entry

Every proposed SDR experiment must be registered under SAGE's Experiment Registry schema. The first simulation's registry entry is defined as:

```json
{
  "experiment_id": "sdr_exp_governance_lifecycle_001",
  "experiment_name": "SAGE Governance Lifecycle Validation Pilot",
  "research_objective": "Validate the complete SAGE governance loop from proposal to archive under mock execution.",
  "responsible_coordinator": "SAGE Supervisor",
  "participating_agents": ["agent_chatgpt", "agent_jules", "agent_claude"],
  "simulation_boundary": "sage/experimental/sdr/scratch/",
  "protected_systems_excluded": ["sage/runtime/", "sage/core/", "sage/acr/"],
  "expected_evidence_output": "evidence_capture/sdr_exp_001_evidence_package.json",
  "validation_criteria": [
    "verify_all_ten_evidence_artifacts_exist",
    "verify_zero_protected_directory_writes",
    "verify_unbroken_traceability_hashes"
  ],
  "reviewer_identity": "independent_auditor_claude",
  "archive_destination": "Main Archive/sdr_exp_governance_lifecycle_001_archive.json",
  "lifecycle_state": "proposed"
}
```

---

## Section 4 — Validation Requirements

During execution, the SAGE SDR runtime must programmatically enforce five validation parameters:

1. **Identity Verification:** Confirm that every message or handoff in the simulation is associated with an active, registered agent node ID (`participating_agents`).
2. **Boundary Verification:** Monitor file I/O operations dynamically. Any write target outside `simulation_boundary` triggers an immediate SPEK violation.
3. **Input / Output Capture:** Intercept and serialize all prompts, payloads, generated code, and results.
4. **Traceability Records:** Ensure every handoff includes a unique secure hash linking back to the preceding step, preserving the unbroken SAGE Agent Continuity Tree.
5. **Failure Capture:** Log and report any failed validations, syntax exceptions, or boundary warnings without interrupting the orchestration daemon's monitoring.

---

## Section 5 — Evidence Package Definition

Upon completion, the SDR orchestrator must compile exactly ten required evidence artifacts into a single structured JSON package:

1. **`experiment_description` (`str`):** Detailed narrative of the simulated run.
2. **`inputs` (`dict`):** The configuration and initial workspace state fed to the agents.
3. **`outputs` (`dict`):** Mock code or documentation files generated by the agents.
4. **`agent_participation_record` (`list[dict]`):** Specific trace of each agent node's contribution and signature.
5. **`timestamps` (`dict`):** Start, handoff, and completion times in UTC format.
6. **`logs` (`list[str]`):** Comprehensive standard outputs recorded during execution.
7. **`validation_results` (`dict`):** Programmatic validator outputs.
8. **`failure_records` (`list[dict]`):** Any caught exceptions or boundary alerts.
9. **`review_conclusion` (`dict`):** Notes, reviewer role, and approved/rejected state.
10. **`archive_reference` (`str`):** designated file path inside the Master Archive.

---

## Section 6 — Human Governance Checkpoints

To ensure complete accountability, SAGE integrates three non-bypassable human checkpoints:

- **Checkpoint 1: Pre-Execution Signoff**
  - *Required before:* Experiment start (`lifecycle_state` transitions from `proposed` to `active`).
  - *Action:* SAGE supervisor must manually approve the registry entry, verifying directories excluded.
- **Checkpoint 2: Evidence Acceptance Signoff**
  - *Required before:* Transitioning to Independent Review.
  - *Action:* Reviewer inspects the collected logs and validation results, verifying evidence completeness.
- **Checkpoint 3: Archive Promotion Signoff**
  - *Required before:* Capability passport state promotion (`PROPOSED` to `VALIDATED` in INDEX.md).
  - *Action:* SAGE supervisor signs off the final review gate notes, permanently archiving the receipt.

---

## Section 7 — Failure Conditions

The experiment is instantly aborted and flagged as `failed` if any of the following triggers occur:
- **Invalid Evidence:** One or more of the ten required evidence artifacts are missing or unreadable.
- **Boundary Violation:** Any attempt to read, write, or access files outside the authorized scratch directories.
- **Missing Records:** Incomplete handoff timestamps or unsigned agent payloads.
- **Unclear Ownership:** Payload inputs or outputs with missing author/agent identifiers.
- **Failed Validation:** Programmatic syntax or Ast checkers fail to validate mock output code.

---

## Section 8 — Frozen Boundaries

The following core systems and research items are **frozen** from any simulation-driven change:
- **No Production Activation:** The simulation scratch code remains strictly isolated and will never run as a production worker or background service.
- **No Autonomous Agents:** Simulated agents are triggered programmatically via a deterministic test script; no autonomous planning or self-directed execution loop is enabled.
- **No Runtime Modification:** The SAGE runtime files (`engine.py`, `api.py`, etc.) are completely read-only.
- **No Capability Promotion:** The capability under test is strictly a mock and will not update standard system endpoints or core middleware validation logic.
