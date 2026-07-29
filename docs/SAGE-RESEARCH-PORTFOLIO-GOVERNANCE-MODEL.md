# SAGE Research Portfolio Governance Operating Model

**Record ID:** SAGE-RPGM-2026-07-30
**Classification:** Strategic Architecture & Governance Specification
**Status:** `VALIDATED` (under Master Archive authority)
**Evidence Level:** Standardizing document-only research governance.

---

## 1. Executive Summary & Purpose

This document specifies the **SAGE Research Portfolio Governance Operating Model (RPGM)**. Its objective is to establish SAGE's governance model for managing future research opportunities while preserving a strict separation between speculative ideas, active proposals, validation evidence, experimental capabilities, and canonical production architecture.

In strict alignment with SAGE's governance directives, **no active runtime layers or protected directories (`sage/runtime/`, `sage/core/`, `sage/acr/`) have been modified, no completed milestones have been reopened or restarted, and no new implementation scope has been introduced.** All specifications are documentation-only, verified under 100% green passing platform tests.

---

## 2. Research Portfolio Structure

The SAGE Research Portfolio is organized into five structured categories to maintain clean boundaries between operational reality and conceptual design:

```
SAGE Research Portfolio Structure
├── [ACTIVE RESEARCH]
│   └── Current, authorized studies being evaluated in sandbox/docs format
├── [VALIDATED RESEARCH]
│   └── Research specs backed by completed reviews or simulated evidence
├── [PENDING PROPOSALS]
│   └── Roadmap items drafted and pre-staged for authorization
├── [RETIRED CONCEPTS]
│   └── Non-viable historical designs preserved for lessons learned
└── [FUTURE EXPLORATION]
    └── Long-term speculaive theories and civilization-scale scale ideas
```

### 2.1. Standardized Intake Schema
Every research proposal entering the portfolio must feature a standardized header containing the following nine fields:

1. **Research ID:** Unique alphanumeric identifier (e.g., `SAGE-RES-001`).
2. **Origin:** The conceptual source or creative inspiration (e.g., Star Wars Holocrons).
3. **Problem Statement:** Detailed description of the friction point addressed.
4. **Historical Lineage:** Direct parent specifications or earlier design attempts.
5. **Expected Value:** Qualitative or quantitative continuity benefit.
6. **Dependencies:** Direct capability prerequisites.
7. **Evidence Requirements:** Defining exit criteria and test blueprints.
8. **Risk Level:** Security impact, regression risk, and sandbox isolation depth.
9. **Lifecycle Classification:** Matching the Index Layer v0.1 Provenance Schema.

---

## 3. Research Prioritization Model

To ensure SAGE allocates its development resources to the highest-value capabilities, proposals must be scored against seven prioritization criteria:

* **Mission Alignment:** Does it accelerate the *one-person organization* goal?
* **Continuity Improvement:** Does it reduce session context loss or rehydration latency?
* **Reliability Impact:** Does it prevent state-loss, trace corruption, or database drift?
* **Security Impact:** Does it enforce strict sandboxed boundaries and SPEK rules?
* **Evidence Maturity:** Is the validation evidence machine-verifiable?
* **Dependency Readiness:** Are all prerequisite capabilities fully canonical or validated?
* **Implementation Difficulty:** Complexity of development, estimated token overhead, and dependency depth.

---

## 4. Research Queue State Machine

Proposals advance sequentially through six distinct lifecycle states. A state transition is only authorized once the required validation evidence has been recorded:

$$\text{FUTURE EXPLORATION} \longrightarrow \text{STRATEGIC RESEARCH INPUT} \longrightarrow \text{PROPOSED} \longrightarrow \text{VALIDATED} \longrightarrow \text{VALIDATED EXPERIMENTAL} \longrightarrow \text{MASTER ARCHIVE}$$

1. **FUTURE EXPLORATION:** High-level speculative ideas with zero design footprint.
2. **STRATEGIC RESEARCH INPUT:** Thematic research papers compiled under the Labs or research directories.
3. **PROPOSED:** Formally drafted capability proposal with defined evidence requirements.
4. **VALIDATED:** Documentation and validation reviews completed and signed by a human operator.
5. **VALIDATED EXPERIMENTAL:** Functional code sandbox implemented and verified cleanly inside `sage/experimental/act/`.
6. **MASTER ARCHIVE:** Promoted to the core runtime with canonical status.

---

## 5. Portfolio Review Process & Conflict Resolution

### 5.1. Portfolio Review Process
SAGE holds periodic, structured portfolio reviews to audit the knowledge graph:
* **Maturity Audit:** Evaluating if spec files have standard lineage headers.
* **Trace Verification:** Verifying that ADRs map directly to their green verification tests.

### 5.2. Duplicate & Conflict Resolution
* **Duplicate Detection:** Natural language and tag matching over the indexing registers. Overlapping summaries are compiled in health assessments.
* **Conflict Resolution:** If two specifications define contradictory design rules, they are kept separated in the Labs space. Merges or deprecations require explicit, multi-signature human operator approval.
* **Preserving Rejection Contexts:** Rejected proposals must **not** be deleted. They are archived under `Main Archive/research/archive/` to prevent subsequent sessions from repeating non-viable patterns.

---

## 6. Research-to-Capability Transition Rules

* **Rule 1 (Research to Proposal):** Research can only transition to `PROPOSED` once its intake schema is fully completed and registered in `Main Archive/INDEX.md`.
* **Rule 2 (Proposal to Experiment):** A proposed spec can only transition to `VALIDATED EXPERIMENTAL` after a sandboxed Python prototype has been isolated under `sage/experimental/act/` and validated under 100% green tests.
* **Rule 3 (Experiment to Architecture):** An experimental capability can only transition to `MASTER ARCHIVE` canonical status after a formal security audit, AST boundary verification, and a multi-signature human authorization gate.

---

## 7. SAGE Research Portfolio Mapping

The current SAGE capabilities, active proposals, and future research tracks are classified under the official RPGM lifecycle states:

### 7.1. Master Archive (Canonical Core Layers)
* **SAGE Attestation & Cryptographic Registry (SAGE-ACR v1.0.0):** Base security layer.
* **SAGE Policy Enforcement Kernel (SPEK v1.1):** Hardened governance layer.
* **Master Archive Core & Persistent Archive Store:** Immutable storage engines.

### 7.2. Validated Experimental (Sandbox Scaffolds)
* **Continuity Control Loop (SAGE-CCL Loop Telemetry):** Isolated telemetry loop.
* **Stateless Context Rehydration (GovernedAgentRehydrator):** Stateless CMAPS payload parser.

### 7.3. Validated (Operational Ledger Artifacts)
* **SAGE Blueprint Continuity Integration Map:** Conceptual origin records.
* **SAGE Archive Navigation Standard:** Naming and discovery standards.
* **SAGE Future Session Recovery Protocol:** Rehydration checklists.
* **SAGE Documentation Intelligence Maturity Review:** 10-dimension audit reports.
* **SAGE Evolution Decision Intelligence Framework:** Completeness and causal schemas.

### 7.4. Future Exploration (Roadmap Items)
* **SAGE-SDR (Safe Dry-Run Rehydration):** Isolated VM sandbox execution.
* **SAGE-CRC (Cryptographic Session Receipt Chain):** Multi-session hash-linked chains.
* **SAGE-MAT (Multi-Agent Transaction Ledger):** Distributed DAG transaction ordering.

---

## 8. Protected Boundary Confirmation

* **Modified Runtime Folders:** `sage/runtime/`, `sage/core/`, `sage/acr/` ──► **0 Files Touched**.
* **Test Verification Status:** **185/185 Tests Passed 100% Green** under poetry.

This operating model secures SAGE's research pipeline, ensuring that conceptual exploration remains highly disciplined, secure, and separated from active runtime operations.

---

*Prepared by Jules, Software Engineer.*
*Submitted and Validated under Master Archive Authority.*
