# SAGE Decision Traceability Matrix

**Record ID:** SAGE-DTM-2026-07-30
**Classification:** Strategic Research & Decision Ledger
**Status:** `VALIDATED` (under Master Archive authority)
**Evidence Level:** Non-mutating decision tracing.

---

## 1. Introduction

The **SAGE Decision Traceability Matrix (DTM)** traces SAGE's core architectural decisions. By documenting the rationales, alternative choices, rejection justifications, evidence files, and downstream dependencies of each major decision, SAGE ensures absolute accountability and prevents historical reasoning drift across sessions.

---

## 2. Core Decision Traceability Ledger

### 2.1. Decision 1: Establishing SAGE-ACR Cryptographic attestation (ADR-001)
* **Why Proposed:** To guarantee session authenticity and prevent trace-tampering by external collaborator agents or unverified runs.
* **Problem Solved:** Vulnerability to transaction spoofing, trace injection, and nonce-replay attacks in distributed sessions.
* **Alternatives Considered:**
  * *Standard database session variables (unhashed).*
  * *Reason for Rejection:* Lacked cryptographic integrity; database compromises could allow retroactive trace manipulation.
* **Supporting Evidence:** `tests/test_acr.py`, `tests/test_api_auth.py`, and `sage/acr/attestation.py` (implementing HMAC signature verification and attestation bonds).
* **Current Lifecycle State:** `CANONICAL` (Core Production Layer).
* **Related Documents:** `Main Archive/adr/ADR-001-architecture-baseline.md`.
* **Future Dependencies:** Direct foundation for Milestone 3 rehydrators and Milestone 5 auditors.

### 2.2. Decision 2: Implementation of SPEK v1.1 Hardened Kernel
* **Why Proposed:** To prevent autonomous agents from mutating active production systems or bypassing core governance policies.
* **Problem Solved:** Runaway evolutionary drift ("black goo" mutations) where an AI agent could modify core configuration files or bypass write boundaries.
* **Alternatives Considered:**
  * *Standard Git branch permissions only.*
  * *Reason for Rejection:* Git-level checks operate too late in the development cycle; they cannot prevent runtime state corruptions inside the live container.
* **Supporting Evidence:** `tests/test_spek.py` and `sage/core/spek.py` (enforcing hardened policy rules, audit trails via `spek_vault.json`, and transaction safety).
* **Current Lifecycle State:** `CANONICAL` (Core Production Layer).
* **Related Documents:** `SAGE Constitution (CONSTITUTION.md)`.
* **Future Dependencies:** Governs all promotions from Layer 2 (Working Evidence) to Layer 3 (Immutable Ledger).

### 2.3. Decision 3: Standardizing on CMAPS v1.0
* **Why Proposed:** To establish a model-neutral, structured, and machine-validatable currency for exchanging execution traces and failure evidence.
* **Problem Solved:** Fragmentation of trace formats across Anthropic Claude, OpenAI ChatGPT, and Google Gemini models, which prevented automatic validation of recovery paths.
* **Alternatives Considered:**
  * *Ingesting raw, model-specific conversational text logs.*
  * *Reason for Rejection:* Raw texts cannot be programmatically validated for chronological invariants (e.g. `started_at <= updated_at`) and are highly prone to prompt injections.
* **Supporting Evidence:** `tests/experimental/test_cross_model_audit_schema.py` and `sage/experimental/act/contracts.py` (validating format, relational, and cryptographic invariants).
* **Current Lifecycle State:** `Architecturally Stabilized Candidate Path` (Strategic Research Track).
* **Related Documents:** `docs/SAGE-CROSS-MODEL-AUDIT-PAYLOAD-SCHEMA.md`.
* **Future Dependencies:** Foundation for SAGE-SDR rehydration pipelines and SAGE-CRC session chains.

### 2.4. Decision 4: Quarantine of Experimental ACT (One-Way Import Law)
* **Why Proposed:** To enable rapid experimentation on context rehydration and lineage verification without introducing risks of core runtime instability.
* **Problem Solved:** Untested or active research code leaking into pristine core production systems, risking baseline regression.
* **Alternatives Considered:**
  * *Developing experimental features directly inside `sage/acr/session/`.*
  * *Reason for Rejection:* Violated SAGE’s absolute isolation rule; any typo in experimental code could prevent the container from booting or pass verification tests with false-positives.
* **Supporting Evidence:** `tests/test_runtime_contract.py` (enforcing AST-level import quarantine rules).
* **Current Lifecycle State:** `VALIDATED` (Experimental Quarantine Framework).
* **Related Documents:** `docs/SAGE-EVOL-001-CONFLICT-RESOLUTION-REPORT.md`.
* **Future Dependencies:** Mandatory sandbox architecture for all future milestones (Milestones 3, 4, and 5).

---

## 3. Decision Traceability Matrix Table

The following matrix table maps major decision nodes to their associated specs, verification tests, and downstream research vectors:

| Core Decision Node | Associated Spec File | Verification Test | Downstream Research |
|---|---|---|---|
| **SAGE-ACR Attestation** | `ADR-001-architecture-baseline.md` | `tests/test_acr.py` | `SAGE-CRC Session Chain` |
| **SPEK Policy Kernel** | `CONSTITUTION.md` | `tests/test_spek.py` | `SAGE-MAT Transaction Ledger` |
| **CMAPS Trace Schema** | `SAGE-CROSS-MODEL-AUDIT-PAYLOAD-SCHEMA.md` | `test_cross_model_audit_schema.py` | `SAGE-SDR Dry-Run Pipeline` |
| **ACT Experimental Quarantine**| `SAGE-EVOL-001-ARCHITECTURE-ACCEPTANCE-RECORD.md`| `test_runtime_contract.py` | `Milestone 5 (SAGE-ACT-SRACA)` |

---

*Prepared by Jules, Software Engineer.*
*Submitted and Validated under Master Archive Authority.*
