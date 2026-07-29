# SAGE Future Session Recovery Protocol

**Record ID:** SAGE-FSRP-2026-07-30
**Classification:** Documentation Governance Standard
**Status:** `VALIDATED` (under Master Archive authority)
**Evidence Level:** Standardizing document-only recovery protocols.

---

## 1. Executive Summary & Purpose

The purpose of the **SAGE Future Session Recovery Protocol (FSRP)** is to define the exact sequence of actions that an incoming developer session or AI collaborator must execute to instantly rehydrate SAGE's operational, strategic, and historical context. By following this step-by-step protocol, new sessions prevent context decay, eliminate cognitive startup latency, and ensure absolute compliance with SAGE's governance boundaries.

---

## 2. Step-by-Step Context Rehydration Protocol

When initiating a new SAGE session, the incoming agent must execute the following rehydration steps in sequence:

```
┌────────────────────────────────────────────────────────┐
│  Step 1: Locate and Parse Master Archive Index          │
│  - Load Main Archive/INDEX.md to find all active specs │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Step 2: Load Canonical Constitution & Core Boundaries  │
│  - Parse CONSTITUTION.md & SPEK rules to set safety keys│
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Step 3: Read Collaborator Orientation Layer           │
│  - Load SAGE_GOOGLE_ALIGNMENT_WRAP.md for role maps   │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Step 4: Synchronize Historical Design Lineage         │
│  - Parse SAGE-BLUEPRINT-CONTINUITY-INTEGRATION.md      │
└───────────────────────────┬────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────┐
│  Step 5: Verify Active Capabilities & Test Baseline   │
│  - Run pytest to verify 185/185 green tests           │
└────────────────────────────────────────────────────────┘
```

### 2.1. Step 1: Locate and Parse the Master Archive Index
* **Action:** Load and parse `Main Archive/INDEX.md` (The Canonical Index).
* **Objective:** Map the entire documentation ecosystem, locating the path and Record ID of every validated and proposed file.

### 2.2. Step 2: Load the Canonical Constitution & Core Boundaries
* **Action:** Load and parse `docs/master/CONSTITUTION.md`.
* **Objective:** Rehydrate SAGE's core architectural constraints, governance laws, and SPEK policy boundaries (such as the One-Way Import Law).

### 2.3. Step 3: Read the Collaborator Orientation Layer
* **Action:** Load and parse `docs/SAGE_GOOGLE_ALIGNMENT_WRAP.md`.
* **Objective:** Establish the multi-role collaborator boundaries, mapping ChatGPT (Architecture), Claude (Auditor), Google AI (Research), and Jules (Sandboxed Runner) responsibilities.

### 2.4. Step 4: Synchronize Historical Design Lineages & Decisions
* **Action:** Load and parse `Main Archive/research/strategic/SAGE-BLUEPRINT-CONTINUITY-INTEGRATION.md` and `docs/SAGE-DECISION-TRACEABILITY-MATRIX.md`.
* **Objective:** Sync SAGE’s origin, creative metaphors (Marvel, Star Wars, Prometheus), biological comparisons, rejected concepts, and major architectural decisions to prevent recreating non-viable architectures.

### 2.5. Step 5: Verify Active Capabilities & Test Baseline
* **Action:** Execute the automated test suite (`poetry run pytest`).
* **Objective:** Verify that the platform test baseline is exactly 185 green passing tests under strict experimental isolation, confirming zero state-drift.

---

## 3. Location Protocols for Core Assets

When a future session needs to answer a specific architectural question or locate evidence, it must refer to the following authoritative paths:

* **Current Canonical State:** Reference `docs/master/MASTER_SNAPSHOT.md` and `Main Archive/INDEX.md`.
* **Active Research Tracks:** Reference `Main Archive/research/strategic/` Spec documents (such as SME, SRL, SKAL, and BTQI).
* **Validated Capabilities:** Reference `Main Archive/INDEX.md` under state `VALIDATED` or `CANONICAL`.
* **Open Proposals:** Reference `Main Archive/INDEX.md` under state `PROPOSED`.
* **Historical Reasoning & Rejected Approaches:** Reference `Main Archive/research/strategic/SAGE-BLUEPRINT-CONTINUITY-INTEGRATION.md` Sections 4 and 5.
* **Evidence Records & Decision History:** Reference `docs/SAGE-DECISION-TRACEABILITY-MATRIX.md` and individual test suites (e.g., `tests/test_spek.py`).
* **Master Archive Authority:** Confirmed as `Main Archive/` and `docs/master/`.

---

## 4. Multi-Turn Session Rehydration Workflow

To maintain context across virtual machine recycles and multi-turn sessions, SAGE utilizes the following rehydration workflow:

1. **Checkpoint Recovery:** Before modifying any code, the agent searches the checkpoint ledger (`sage/acr/session/checkpoint.py` data files) to find the most recent Git commit, dirty files, and validation states.
2. **Context Tracker Traversal:** Load the active context history via the `ContextTracker` (`sage/acr/session/context_tracker.py`), retrieving recent tasks, objectives, and decisions linked to the session.
3. **Receipt Verification:** Query SAGE-ACR to verify that the loaded session hashes match the latest signed receipts, preventing trace corruption.

---

*Standardized and Validated under Master Archive Authority.*
