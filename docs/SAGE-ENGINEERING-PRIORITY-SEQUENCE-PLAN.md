# SAGE Engineering Priority Sequence Plan

This document establishes a controlled, evidence-based engineering priority roadmap for the **SAGE Autonomous Continuity Runtime**. It translates governance readiness and architectural specifications directly into a prioritized, phased implementation sequence.

This document serves as an engineering blueprint and does **not** execute any production code mutations. All changes are managed under the strict supervision of SAGE’s Capability Evolution Governance Framework, preserving protected boundaries (`sage/runtime/`, `sage/core/`, `sage/acr/`).

---

## 1. Engineering Baseline Summary

SAGE maintains a highly structured multi-agent architecture with zero state drift and an extremely healthy codebase (196/196 passing tests). The baseline is characterized by:
1. **Fully Stabilized Governance:** Strict policies prevent core directory mutation, circular imports, and unauthorized transitions.
2. **Robust REST and Webhook Ingestion:** Fully operational FastAPI endpoints support external payload ingestion, self-verification, and deterministic intake.
3. **Advanced Experimental Foundation:** Fully verified schema structures (CMAPS) and multi-agent contracts (SAGE-ACT Milestones 1 and 2) exist in the codebase but remain decoupled from core, live operational API paths.

---

## 2. Runtime Stabilization Priorities

To transition successfully to controlled production hosting (e.g., Render), high-impact environmental and runtime risks must be resolved first.

### 2.1 High-Impact Blockers & Deployment Risks

1. **State Persistence Limitations (Render Free Tier):**
   - *Risk:* In-memory mode is stateless. Container restarts or scale-downs on Render completely wipe out the runtime's local memory store, active decisions, and session states.
   - *Stabilization Action:* Integrate a periodic or trigger-based background thread that serializes/flushes in-memory state snapshots to a configured backup directory (such as `.sage/`), making recovery seamless on container rehydration.

2. **Google Workspace Sync Blockers:**
   - *Risk:* If `GOOGLE_WORKSPACE_CREDENTIALS_PATH` is missing or invalid, live synchronization calls raise unhandled `FileNotFoundError` or authentication failures, blocking tool integration pathways.
   - *Stabilization Action:* Implement a mock-resilient, graceful degradation mode. If OAuth credentials are not found, the service must report a degraded sync status via `/health` or `/status` instead of raising runtime exceptions.

3. **External API and Auth Key Exposure:**
   - *Risk:* If `SAGE_REQUIRE_AUTH` is enabled, the server relies on dynamic API keys or environment secrets. A missing key immediately blocks all incoming webhook configurations or Custom GPT queries.
   - *Stabilization Action:* Establish a secure default API key fallback for local/non-production environments, and log dynamic key retrieval paths clearly during SAGE's initialization sequence.

---

## 3. Architecture-to-Code Gaps Mapping

An analysis was conducted to map the Master Archive’s architectural claims against the actual repository implementation files, highlighting the integration status of each component.

| Spec / Component | Primary Path | Target State | Existing Status | Identified Gap |
| :--- | :--- | :--- | :--- | :--- |
| **SAGE SPEK Policy Kernel** | `sage/core/spek.py` | Production / Core | **Implemented** | Works as expected, but integration relies on optional environmental `SAGE_BOND_MODE` settings. |
| **SAGE-ACT Lineage Tree (M1/M2)** | `sage/experimental/act/contracts.py` | Operational API Integration | **Experimental / Partially Implemented** | Read-only validator classes are fully tested but are completely decoupled from active FastAPI routes (e.g., `/validate` and `/promote`). |
| **Cross-Model Audit Schema (CMAPS)** | `sage/experimental/act/contracts.py` | Active Ingestion Gate | **Experimental / Partially Implemented** | Programmatic validation works perfectly in isolation but has no operational hook inside active REST routes or webhooks. |
| **SAGE-SDR Safe Dry Run** | N/A | Dry-run Sandbox runner | **Missing / Placeholder** | Exists strictly as a conceptual and readiness design specification with no executable runner code. |
| **SAGE-CCL Continuity Loop** | `sage/runtime/engine.py` | Implicit Workflow event collector | **Partially Implemented** | Ingestion of session payloads is fully functional, but automated daemon tracking of workflow events is not implemented. |

---

## 4. Engineering Sequence Proposal

The implementation sequence is structured into four sequential, dependency-ordered phases. Each phase requires a clear validation and promotion checkpoint before the next can proceed.

### Phase 1: Runtime Reliability Foundation
Focuses on securing environment setup, environmental key fallbacks, and stateless resilience.
- **Milestone 1.1: Stateless Backup Persistence**
  - Implement a silent background worker or trigger-based state flushing loop to backup the database to `.sage/` directory upon major state-changing mutations.
- **Milestone 1.2: Resilient Integration Fallbacks**
  - Establish robust, non-crashing try-except wrappers and mock diagnostics for Google Workspace credentials lookup and ChatGPT/Gemini wrapper modules.

### Phase 2: Validation Infrastructure Strengthening
Focuses on promoting experimental validation contracts directly into operational core API boundaries.
- **Milestone 2.1: Operational SAGE-ACT Validation Integration**
  - Bridge the read-only `SessionStateTaskLinker` and `TaskDecisionBinder` classes directly into the `/validate` and `/promote` endpoints in `sage/api.py`.
- **Milestone 2.2: CMAPS Webhook Enforcement**
  - Integrate the `CrossModelAuditPayloadValidator` as a mandatory validation gate for `/tools/skal/intake` payloads, replacing passive intake parsing with strict CMAPS schema checks.

### Phase 3: Experimental Capability Preparation
Focuses on preparing the sandboxed simulation layer for safe dry-run executions.
- **Milestone 3.1: SAGE-SDR Simulation Sandbox**
  - Create a new submodule `sage/experimental/sdr/` to house the dry-run simulation engine, enabling dry-runs of multi-agent tasks in a completely isolated memory space.

### Phase 4: Future Controlled Implementation Candidates
Focuses on advanced coordination systems and transaction ledgers.
- **Milestone 4.1: SAGE-MAT (Transaction Ledger)**
  - Design and implement read-only ledgers to audit multi-agent interactions, strictly aligned under SAGE’s Parallel Validation Strategy Framework.

---

## 5. Risk Controls & Governance Flow

Every engineering transition is governed by the core lifecycle flow:
$$\text{Research} \rightarrow \text{Validation} \rightarrow \text{Evidence} \rightarrow \text{Human Review} \rightarrow \text{Master Archive}$$

### 5.1 Verification and Quality Gates
- **Import Rules Compliance:** All newly proposed implementation files must strictly reside under `sage/experimental/` during Phase 1-3. No direct code alterations are allowed in `sage/runtime/`, `sage/core/`, or `sage/acr/`.
- **Programmatic Coverage Threshold:** Any new bridge or validation hook must be covered by a corresponding unit or integration test in `tests/experimental/`, preserving the repository's 100% test coverage baseline.
- **API Boundary Protection:** Operational REST endpoints must require valid api keys if `SAGE_REQUIRE_AUTH` is active, maintaining strict boundary validation.

---

## 6. Frozen Items (Requiring No Action)

The following components are fully stabilized and **frozen** from further modification or adaptation:
1. **Core Attestation & Cognitive Hypervisor (`sage/acr/control_plane.py`):** Fully complete, stable, and sealed.
2. **SAGE SPEK Engine (`sage/core/spek.py`):** Stable kernel implementation, completely sealed from code changes.
3. **Index Layer v0.1 Provenance Schema:** The states (`PROPOSED`, `VALIDATED`, `ARCHIVE_CANDIDATE`, `CANONICAL`) are locked.

---

## 7. Recommended First Implementation Milestone

The first recommended execution milestone is **Milestone 1.1: Stateless Backup Persistence**. This milestone delivers maximum resilience for SAGE container environments on Render's Free Tier by enabling automated state serialization and rehydration, converting high-impact data-loss risks into a robust operational baseline.
