# SAGE Evidence Package Specification

**Record ID:** SAGE-ACT-EPS-2026-07-29
**Classification:** PROPOSED — Validation Infrastructure Design
**Status:** PROPOSED
**Target Domain:** SAGE Evidence Validation and Future Render Observations

---

## 1. Evidence Package Purpose

### 1.1 Why Standardized Evidence Artifacts Are Required
As SAGE evolves as a model-independent AI Reliability Infrastructure and Agent Governance Control Layer, verifying the correctness, safety, and continuity of agents across multiple environments becomes critical. Standardized evidence artifacts are required to establish an immutable, verifiable, and structured ledger of execution history. Without standardization, validation data remains scattered, inconsistent, and highly dependent on specific execution environments, preventing automated cross-environment verification.

### 1.2 How Evidence Differs from Raw Logs
* **Raw Logs:** Contain unstructured, high-volume stdout/stderr diagnostic outputs, timing details, and system-level trace information. Logs are context-agnostic, ephemeral, and prone to noise.
* **Evidence Packages:** Are structured, curated, and context-aware records that bind a specific execution attempt to its architectural objectives, cryptographic signatures, and boundary compliance checks. Evidence packages capture semantic meaning rather than raw execution noise.

### 1.3 How Evidence Supports Validation Decisions
Evidence packages provide machine-validatable assertions and human-interpretable lineages. By mapping decisions back to specific state snapshots and cryptographic proofs, they allow validation authorities to programmatically verify that an agent operated within its permitted boundaries before authorizing any state transition or architecture promotion.

### 1.4 How Evidence Reduces Manual Review Burden
By standardizing the schema of validation outcomes, automated compliance tools (such as static analysis and AST checks) can pre-screen evidence packages. Human reviewers only need to inspect high-level assessments and boundary compliance records, transforming the governance workflow from manual traceback to exception-based review.

---

## 2. Evidence Package Structure

Every SAGE Evidence Package must contain the following 18 required fields, formatted as a structured JSON/YAML payload:

1. **Experiment ID:** A unique, monotonically increasing identifier for the validation experiment run (e.g., `EXP-ACT-001`).
2. **Observation ID:** A unique UUID associated with the specific observation capture event (e.g., `OBS-550e8400-e29b-41d4-a716-446655440000`).
3. **Timestamp:** An ISO 8601 UTC timestamp indicating exactly when the evidence was captured (e.g., `2026-07-29T12:00:00Z`).
4. **Environment Information:** Metadata detailing the execution host, environment variables, operating system, and virtual environment state (e.g., Python version, Poetry dependencies, Render service ID).
5. **Scenario Classification:** The type of test scenario being executed (e.g., `STANDARD_EXECUTION`, `OUT_OF_BOUNDS_INTERCEPT`, `REPLAY_ATTACK_SIMULATION`, `TIMEOUT_REHYDRATION`).
6. **Objective:** A concise statement of the specific capability or behavior being validated (e.g., "Verify that the rehydrator rejects a duplicate nonce").
7. **Expected Behavior:** The precise success criteria and architectural invariants expected during execution.
8. **Observed Behavior:** The actual runtime execution outcome, including state transitions and decision outputs.
9. **State Snapshot:** A serialized state representation (e.g., CMAPS-compliant JSON) of the agent's memory, variables, and stack frames at the moment of capture.
10. **Dependency Map:** A list of active imports, third-party libraries, and core/experimental dependencies loaded during the run.
11. **Decision Trace:** A chronological log of decisions made by the agent, mapped directly to their causal justifications.
12. **Artifact References:** URI or file path references to associated files, logs, or persistent storage entries (e.g., `docs/SAGE-CAPABILITY-TREE-HEALTH-ASSESSMENT-REPORT.md`).
13. **Failure Records:** Detailed diagnostic payloads if the run terminated exceptionally, mapping directly to `AgentBoundaryInterceptionError` or other custom exceptions.
14. **Integrity Results:** Cryptographic verification results (e.g., HMAC-SHA256 signature checks and nonce freshness checks).
15. **Boundary Compliance Record:** A boolean flag and matching metadata asserting whether the One-Way Import Law was preserved during execution (i.e., zero imports from `sage/experimental/` to `sage/core/`).
16. **Reviewer Assessment:** A markdown section reserved for manual human evaluation, qualitative feedback, and reviewer signatures.
17. **Lifecycle Classification:** The target status of the validated artifact (e.g., `PROPOSED`, `VALIDATED EXPERIMENTAL`, `VALIDATED`).

---

## 3. Evidence Lifecycle Flow

The progression of an evidence artifact from initial generation to final archival status follows a strict, unidirectional governance pipeline:

```
        Observation
             │
             ▼
      Evidence Capture
             │ (Structured Evidence Package Formulated)
             ▼
      Evidence Review
             │ (Automated & Manual Boundary Check)
             ▼
   Research Interpretation
             │ (Maturity & Gaps Evaluated)
             ▼
     Validation Decision
             │ (Authorization / Rejection Signal Issued)
             ▼
  Master Archive Reference
             │ (Indexed as VALIDATED or CANONICAL)
             ▼
```

1. **Observation:** A running agent or validation environment (e.g., Render) produces raw execution telemetry.
2. **Evidence Capture:** Raw observations are compiled, validated against this specification, and serialized into an Evidence Package.
3. **Evidence Review:** The package is automatically audited for boundary compliance (One-Way Import Law) and cryptographic signature validity.
4. **Research Interpretation:** Researchers evaluate the package's results to determine maturity, stability, and gap coverage.
5. **Validation Decision:** The governing body (e.g., Supervisor or Agent Control Panel) issues an approval or rejection signal based on the evidence.
6. **Master Archive Reference:** The approved Evidence Package and its associated research documents are indexed and archived in `Main Archive/INDEX.md`.

---

## 4. Evidence Quality Requirements

To be recognized as valid input for architectural or governance decisions, every SAGE Evidence Package must satisfy the following six quality requirements:

* **Completeness:** Every required field in Section 2 must be fully populated. Incomplete packages are automatically rejected at the intake gate.
* **Traceability:** Every decision must be traceably linked to its preceding state snapshot and preceding causal task.
* **Reproducibility:** The environment metadata and scenario details must be sufficient for an independent validator to recreate the exact execution run and observe the same outcome.
* **Consistency:** All timestamps, identifiers, and relational keys must exhibit chronological and logical consistency (e.g., `started_at <= ended_at`).
* **Boundary Compliance:** The package must explicitly prove that no protected runtime modifications occurred and that the One-Way Import Law was fully preserved.
* **Human Interpretability:** Summaries, objective descriptions, and reviewer assessments must be written in clear, concise, and jargon-free markdown.

---

## 5. Evidence Classification

SAGE Evidence Packages and their associated research specifications are classified under the following five lifecycle states:

* **PROPOSED:** Initial design, research proposal, or schema definition prior to experimental implementation.
* **VALIDATED EXPERIMENTAL:** An experimental prototype or capability that has been implemented, validated by 100% test pass rates in `sage/experimental/`, and successfully archived.
* **VALIDATED:** A mature capability or specification that has undergone full validation testing, independent review, and index integration.
* **RETIRED:** Historical or deprecated specifications that are no longer active but remain preserved for genealogical continuity.
* **STRATEGIC RESEARCH INPUT:** High-level strategic modeling, alignment reviews, and cognitive frameworks that inform long-term direction but contain no active codebase components.

---

## 6. Human Review Boundary

* **Evidence Informs, Humans Decide:** Evidence packages are designed to automate telemetry collection and compliance reporting. They provide rich context to human review authorities but **do not possess the authority to self-authorize implementation or state changes**.
* **Zero Self-Promotion:** No experimental result, regardless of test pass rates or success metrics, can be automatically promoted to production core status.
* **Separate Governance Path:** Transitioning from `VALIDATED EXPERIMENTAL` to `CANONICAL` production architecture requires a separate, explicit governance gate, independent audit, and multi-signature supervisor authorization.

---

## 7. Future Render Relationship

### 7.1 Observation Without Control
In future validation cycles, cloud-hosted platforms (such as Render) may serve as the execution host for SAGE agents, generating raw telemetry that is compiled into SAGE-compliant Evidence Packages.

### 7.2 Strict Boundary Enforcement
* **One-Way Data Flow:** Render acts strictly as a read-only observer and execution space. Render-generated packages flow into the research and validation pipelines but cannot alter the SAGE core architecture.
* **No Active Control:** The SAGE Policy Enforcement Kernel (SPEK) and core attestation registries remain the absolute authorities. Render cannot bypass security boundaries, inject unverified code, or dictate lifecycle classifications.
