# SAGE Organism & Jigsaw Architecture Governance Directive

**Directive ID:** `SAGE_ORGANISM_JIGSAW_ARCHITECTURE`
**Version:** `1.0`
**Authority:** SAGE C2 Persistent Operating Contract + Git/main truth + Master Archive Governance

---

## 1. Executive Summary: One Organism, Modular Organs

SAGE is **one governed execution organism with modular organs**. It is governed by a single control/contract spine rather than competing orchestration systems or fragmented brains.

The target architecture unifies all capabilities across an 11-stage continuous pipeline:

```text
                         ┌─────────────────────┐
                         │     CUSTOMER /      │
                         │   MISSION INTENT    │
                         └──────────┬──────────┘
                                    ↓
                         ┌─────────────────────┐
                         │   C2 MISSION CORE   │
                         │ intent / authority  │
                         │ state / boundaries  │
                         └──────────┬──────────┘
                                    ↓
                  ┌──────────────────────────────────┐
                  │      DEEP RECON + SUPER SEARCH   │
                  │ repo truth + external intelligence│
                  └────────────────┬─────────────────┘
                                   ↓
                         ┌─────────────────────┐
                         │  FRONTIER / WAVE    │
                         │     PLANNER         │
                         └──────────┬──────────┘
                                    ↓
               ┌────────────── BIG JUMP WAVE ──────────────┐
               │                                           │
               │ F1   F2   F3   F4   F5                    │
               │ ↓    ↓    ↓    ↓    ↓                     │
               │ RECON → BUILD → TEST → OBSERVE            │
               │       → REPAIR → VERIFY → EVIDENCE        │
               │                                           │
               └────────────────┬──────────────────────────┘
                                ↓
                     ┌──────────────────────┐
                     │   RECONVERGENCE      │
                     │ independent verify   │
                     │ conflict resolution  │
                     └──────────┬───────────┘
                                ↓
                 ┌─────────────────────────────┐
                 │ CUSTOMER / OBSERVATORY HUD  │
                 │ identity / state / outcome  │
                 └──────────────┬──────────────┘
                                ↓
                 ┌─────────────────────────────┐
                 │ EVIDENCE + ECONOMIC MEASURE │
                 └──────────────┬──────────────┘
                                ↓
                 ┌─────────────────────────────┐
                 │ QUALIFY / PROMOTE CAPABILITY│
                 └──────────────┬──────────────┘
                                ↓
                 ┌─────────────────────────────┐
                 │      CAPABILITY WAREHOUSE   │
                 │ knowledge / recovery / reuse│
                 └──────────────┬──────────────┘
                                │
                                └────→ NEXT MISSION
```

Organ roles inside the SAGE Organism:
- **Five Flights (F1–F5):** The limbs (parallel bounded execution paths).
- **C2 Mission Control (`[SAGE::C2::CHATGPT]`):** The coordination and control reasoning system.
- **Super Search / Deep Recon:** The external sensing layer.
- **Jules (`[JULES]`):** The execution and building organ.
- **Gemini (`[GEMINI]`):** The intelligence and research organ.
- **Verification / Reality Gate:** The immune system (fail-closed integrity checks).
- **Evidence / Provenance:** The nervous-system memory (cryptographically signed receipts).
- **Observatory HUD:** The sensory/customer interface.
- **Capability Warehouse:** Long-term learned capability, knowledge graph, and recovery ledger.

---

## 2. The Jigsaw Taxonomy: Subsystem Relationships

Every subsystem, engine, module, and adapter in SAGE must maintain exactly one of four canonical relationships to the organism:

1. **`CORE`** — Authoritative control-plane capability. Defines mission authority, state locks, or primary execution rules (e.g., `SageRuntime`, `FrontierAdmissionEngine`, `ChatGPTC2Contract`).
2. **`SERVICE`** — Specialized capability called by the organism to perform targeted work (e.g., `SuperSearch`, `GeminiReconProbe`, `SupplyChainAttestationFabric`).
3. **`PROJECTION`** — View or interface of canonical state for humans or systems (e.g., Observatory HUD, `CustomerWorkbench`, CLI status).
4. **`EVIDENCE_LEARNING`** — Records and feeds validated outcomes back into the organism (e.g., `CapabilityWarehouseEngine`, `FleetQualificationLedger`, `CCLOutcomeFeedbackBridge`).

### Single Source of Truth & Duplicate Authority Prohibition
- **No Duplicate C2 Authority:** Only `sage/c2/` and `SageRuntime` represent C2 mission control.
- **No Duplicate State Authority:** Repository truth (`git rev-parse HEAD`), Master Archive, and canonical `RuntimeState` hold state. No adapter or external window may maintain disconnected state truth.
- **No Duplicate Workflow Authority:** The 5x4 Big Jump Wave execution frame is the sole canonical workflow engine.

---

## 3. The 10 Connective Tissue Integration Gates

To ensure every molecule of SAGE is hardened, integration testing must verify the 10 connective tissue links spanning the organism:

1. **Gate 1: Mission Intake → C2 Core**
   *Check:* Intent and constraints survive intake without corruption or state drift.
2. **Gate 2: C2 Core → Super Search / Recon**
   *Check:* External research remains attributable, bounded, and repository-first.
3. **Gate 3: Recon → Frontier Planner**
   *Check:* External and internal intelligence correctly alters execution frontiers when warranted.
4. **Gate 4: Frontier Planner → Five Flights**
   *Check:* Independent frontiers are dispatched concurrently without collision or scope overlap.
5. **Gate 5: Five Flights → Evidence Capture**
   *Check:* Every flight action generates cryptographically bound SHA-256 evidence receipts.
6. **Gate 6: Evidence Capture → Independent Verification**
   *Check:* Reality Gate and Reconvergence Synthesizer distinguish verified execution from unproven claims.
7. **Gate 7: Verification → Customer Surface (Observatory HUD)**
   *Check:* Customer-visible identity, HUD, and mission progression accurately project verified state.
8. **Gate 8: Customer Surface → Economic Measurement**
   *Check:* `CustomerWorkbench` measures workflow velocity, cost, value, and intervention savings.
9. **Gate 9: Economic Measurement → Capability Warehouse**
   *Check:* Validated improvements and receipts promote into reusable warehouse capabilities.
10. **Gate 10: Capability Warehouse → Next Mission**
    *Check:* Subsequent missions rehydrate state and start from the upgraded capability baseline.

---

## 4. Anti-Drift and Contract Integration

This directive is bound into `docs/governance/CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT_CONTRACT.md` and `sage/c2/chatgpt_c2_contract.py` as Law 13:

> **Law 13:** SAGE is one governed organism with modular organs. All subsystems map into the Jigsaw taxonomy (`CORE`, `SERVICE`, `PROJECTION`, `EVIDENCE_LEARNING`). No subsystem may maintain duplicate C2, state, or workflow authority.
