# SAGE Multi-Agent Contribution & Attribution Governance Architecture

**Document Version:** 1.0
**Status:** ARCHITECTURAL SPECIFICATION & HARDENING DIRECTIVE
**Scope:** `sage/experimental/airspace/`, `sage/experimental/airspace/points_xp_economy.py`, `sage/c2/`

---

## 1. Context & Architectural Problem

SAGE Airspace currently records an `AirspaceEvent` ledger with a single `actor` string per event, and awards Points/XP directly to a single `station_id` recipient via `PointsXPEconomy.award_points()`.

While this establishes an immutable event trail, it does not represent multi-agent collaboration where multiple stations (e.g. `CHATGPT` for design, `GEMINI` for discovery/root-cause, `JULES` for build, `F1..F5` for verification) participate in the same encounter or mission.

### Core Invariant
> **Participation ≠ Contribution ≠ Reward**

- **Participation:** An agent was demonstrably involved in an encounter.
- **Contribution:** An agent produced an attributable, evidence-backed action or artifact.
- **Reward:** An evidence-backed contribution was verified and converted into Points/Career XP.

---

## 2. Four Canonical Questions

To prevent unearned credit attribution while ensuring multi-agent collaboration is fairly recognized, SAGE separates four distinct operational concerns:

1. **Who performed an action?** (`actor`)
2. **Who was involved in the overall encounter?** (`participants[]`)
3. **What specific work did each participant contribute?** (`contribution_role`)
4. **Who deserves verified Points/XP?** (`verified_contribution_attribution`)

---

## 3. Contribution Roles Taxonomy

SAGE establishes 12 canonical contribution roles across multi-agent encounters:

| Role | Definition | Typical Evidence Primitive |
| :--- | :--- | :--- |
| `DISCOVERED` | Identified a defect, anomaly, or opportunity | Telemetry, test failure, search receipt |
| `ANALYZED` | Diagnosed root cause or failure mechanism | Diagnostic log, autopsy report |
| `DESIGNED` | Formulated architecture or repair strategy | Spec document, C2 contract plan |
| `BUILT` | Implemented code or configuration changes | Git commit SHA, diff, source file |
| `REPAIRED` | Applied targeted fix to failing subsystem | Target kill receipt, clean diff |
| `VERIFIED` | Validated outcome via automated test/probe | Test execution receipt, pytest run |
| `REVIEWED` | Conducted code or policy review | Code review record, audit log |
| `DIRECTED` | Issued high-level C2 mission directive | Authorized mission spec |
| `PROVIDED_INTELLIGENCE` | Supplied external signal or data | External signal receipt |
| `COORDINATED` | Managed multi-vehicle flight concurrency | Concurrency lock receipt |
| `REUSED` | Reused verified substrate without duplication | Subsystem reference, AST graph match |
| `RECOVERED` | Executed automatic state rollback / recovery | Transition recovery receipt |

---

## 4. Lineage & Provenance Authority Chain

The attribution pipeline follows a strict, one-way fail-closed sequence:

```text
RAW ACTIVITY
     │
     ▼
ENCOUNTER / TRACE ID
     │
     ▼
AGENT + ROLE ASSIGNMENT
     │
     ▼
ARTIFACT / ACTION / OUTPUT
     │
     ▼
EVIDENCE COLLECTION (`evidence_refs`)
     │
     ▼
INDEPENDENT VERIFICATION (`verdict = PASS`)
     │
     ▼
CONTRIBUTION LEDGER (`ContributionRecord`)
     │
     ▼
SCORING ENGINE (`PointsXPEconomy`)
     │
     ▼
POINTS AWARDED
     │
     ▼
CAREER XP MINTED (10 Points = 1 XP)
     │
     ▼
CANONICAL ORGANISM PROJECTION
     │
     ▼
CHATGPT / C2 IMMERSION SURFACE
```

### Self-Award Prohibition Law
No agent station (`CHATGPT`, `GEMINI`, `JULES`, etc.) may assign Points to itself or declare its own contribution value. Points/XP allocation is calculated exclusively by the deterministic SAGE scoring engine after verification.

---

## 5. Architectural Data Model: `ContributionRecord`

```json
{
  "contribution_id": "contrib_enc_1042_001_a9f8",
  "encounter_id": "enc_1042",
  "agent_id": "GEMINI",
  "role": "DISCOVERY",
  "evidence_refs": ["EVID-77"],
  "artifact_refs": ["sage/experimental/airspace/career_calibration.py"],
  "verified": true,
  "verification_ref": "test_career_calibration_pass",
  "timestamp": "2026-09-02T21:30:00Z"
}
```

---

## 6. Operating Philosophy: BUILD → OBSERVE → COLLECT → VERIFY

In alignment with SAGE SOTA principles:
1. **Observation First:** Collect real execution evidence across multi-agent campaign flights before hardcoding allocation percentages.
2. **Deterministic Evaluation:** Points attach to verified `ContributionRecord` entries rather than chat participation counters.
3. **Immutable History:** All contribution records persist in `evidence_capture/airspace_ledger.json` as verifiable `AirspaceEvent` payloads.
