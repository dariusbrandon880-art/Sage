# SAGE Capability Dependency Map

**Record ID:** SAGE-CDM-2026-07-30
**Classification:** Strategic Research & Dependency Map
**Status:** `VALIDATED` (under Master Archive authority)
**Evidence Level:** Non-mutating capability dependency mapping.

---

## 1. Introduction

The **SAGE Capability Dependency Map (CDM)** details the sequential and structural dependency relationships across SAGE’s production core modules, experimental continuity trees, and future research tracks. This map tracks dependencies exclusively, ensuring that future milestones proceed with clear structural awareness.

---

## 2. Core Capability Dependency Relationships

The SAGE platform's capabilities are split into three layers (Core, Experimental ACT, and Future Research Tracks). Under SAGE's unidirectional architecture rules, higher layers can depend on lower layers, but lower layers (production core) must **never** depend on higher experimental layers.

```
       ┌────────────────────────────────────────────────────────┐
       │             Layer 1: Production Core Layers            │
       │   - SAGE-ACR, SPEK, Master Archive, Persistent Storage │
       └───────────────────────────┬────────────────────────────┘
                                   │ (One-Way Import Law)
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │         Layer 2: Experimental ACT Capabilities         │
       │   - SAGE-ACT, Stateless Rehydrator, CMAPS v1.0, CCL    │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             Layer 3: Future Research Tracks            │
       │   - SAGE-SDR, SAGE-CRC, SAGE-ACT-SRACA, SAGE-MAT       │
       └────────────────────────────────────────────────────────┘
```

### 2.1. Node Dependencies List
1. **SAGE Attestation & Cryptographic Registry (SAGE-ACR):**
   * *Dependencies:* None. Base infrastructure layer.
2. **SAGE Policy Enforcement Kernel (SPEK v1.1):**
   * *Dependencies:* Base layer. Integrates with the attestation registry to sign compliance receipts.
3. **Master Archive & Persistent Archive Store:**
   * *Dependencies:* Depends on SAGE-ACR (for transaction authentication) and SPEK (to enforce promotion authorization).
4. **SAGE Agent Continuity Tree (SAGE-ACT) Lineage validation:**
   * *Dependencies:* Depends on SAGE-ACR (maps SessionState context to AgentTasks) and SPEK (under One-Way AST isolation).
5. **Continuity Control Loop (SAGE-CCL Loop Telemetry):**
   * *Dependencies:* Depends on SAGE-ACT and the core memory systems.
6. **Cross-Model Audit Schema (CMAPS v1.0):**
   * *Dependencies:* Depends on SAGE-ACT. Standardized as a candidate exchange contract.
7. **Stateless Context Rehydration (GovernedAgentRehydrator):**
   * *Dependencies:* Directly depends on CMAPS v1.0 (to parse payloads) and SAGE-ACR (to re-verify cryptographic signatures).
8. **Active Client Hook (SAGE-ACH Telemetry Intercept):**
   * *Dependencies:* Relies on SAGE-ACT boundaries for telemetry output formatting.
9. **Governance Framework & Evidence Lifecycle:**
   * *Dependencies:* Cross-cutting governance capability regulating all Layer 2 and Layer 3 promotions.
10. **Knowledge Navigation & Historical Recovery / Blueprint Continuity:**
    * *Dependencies:* Relies on the Master Archive index and strategic research spec layers for context mapping.
11. **Reliability and Continuity Gap Analysis & Governed Capability Priority Proposal:**
    * *Dependencies:* Dependent on SAGE-ACT baseline audits and the Master Archive.
12. **SAGE-CRC (Cryptographic Session Receipt Chain) Evaluation:**
    * *Dependencies:* Depends on Stateless Context Rehydration (Milestone 3) and SAGE-ACR.
13. **SAGE-SDR (Safe Dry-Run Rehydration Pipeline) Evaluation:**
    * *Dependencies:* Depends on Stateless Context Rehydration and SAGE-ACH Telemetry Diffs.
14. **Strategic Research Tracks (SME, SRL, SKAL, BTQI, CSC, EIL, EIX, DESP, APM, MEC, CIR, CIC, HSI):**
    * *Dependencies:* Relate to the SAGE 2 Intelligence Layer, depending on the SAGE-ACR base.

---

## 3. Unidirectional Dependency Matrix Table

The following matrix table explicitly documents the unidirectional dependencies of SAGE’s core and experimental components:

| Component | Direct Parent Dependency | Core Prerequisite | Target Sandbox Namespace |
|---|---|---|---|
| **SAGE-ACR** | *None (Base)* | None | `sage/acr/` |
| **SPEK v1.1** | *None (Base)* | None | `sage/core/spek.py` |
| **SAGE-ACT Lineage** | `SAGE-ACR` | Nonce Ledger | `sage/experimental/act/contracts.py` |
| **CMAPS v1.0** | `SAGE-ACT` | Task Schema | `sage/experimental/act/contracts.py` |
| **Stateless Rehydrator** | `CMAPS v1.0` | SAGE-ACR signature check | `sage/experimental/act/rehydrator.py` |
| **SAGE-ACH** | `SAGE-ACT` | Event logging | `sage/experimental/act/active_hook.py` |
| **SAGE-CRC (Future)** | `Stateless Rehydrator` | Multi-session cryptographic hashing | `sage/experimental/act/` (Future Proposal) |
| **SAGE-SDR (Future)** | `Stateless Rehydrator` | Isolation VM boundaries | `sage/experimental/act/` (Future Proposal) |

---

*Prepared by Jules, Software Engineer.*
*Submitted and Validated under Master Archive Authority.*
