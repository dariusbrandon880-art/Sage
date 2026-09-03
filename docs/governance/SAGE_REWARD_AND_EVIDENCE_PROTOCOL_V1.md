# SAGE Reward & Evidence Protocol v1 (`SAGE-RP-1.0`)

**Status:** Canonical Governance Specification
**Authority:** SAGE Autonomous Reward Adjudicator; Git `main` is implementation truth
**Issues:** #426 (Boss Fight Adjudication), #333 (SEP/1 Protocol), #389 (SAGI Brain Integration)

## Executive Summary

The SAGE Reward & Evidence Protocol v1 (`SAGE-RP-1.0`) establishes a versioned, deterministic, and autonomous reward adjudication engine. Progression rewards (verified Points, Career XP, Boss Badges, and Promotion Eligibility) are no longer manually interpreted or assigned by C2 or AI models. Instead, rewards are independently derived from machine-readable `SAGE-SEP/1` evidence packets and persisted to an append-only ledger.

```
                 ┌──────────────────────┐
                 │   EXECUTION / AGENTS │
                 │ GPT / Jules / Gemini │
                 │ Flights / Operators  │
                 └──────────┬───────────┘
                            │
                     VERIFIED REPORT
                            │
                            ▼
                 ┌──────────────────────┐
                 │   SAGE EVIDENCE BUS  │
                 │ immutable receipt    │
                 │ provenance + hashes  │
                 └──────────┬───────────┘
                            │
                            ▼
                 ┌──────────────────────┐
                 │ REWARD ADJUDICATOR   │
                 │ deterministic engine │
                 │                      │
                 │ Points → XP → Badge  │
                 │ → Rank → Promotion   │
                 └──────────┬───────────┘
                            │
                    canonical result
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
       ┌──────────────┐           ┌──────────────┐
       │ SAGE STATE   │           │ C2 FEEDBACK  │
       │ / LEDGER     │           │ report/HUD   │
       └──────────────┘           └──────┬───────┘
                                         │
                                  automatic feedback
                                         │
                                         ▼
                                      SAGI Brain
```

---

## 1. SAGE REWARD LAW 🔒

1. **Protocol Versioning:** Reward formulas and event values are bound to protocol versions (e.g., `SAGE-RP-1.0`).
2. **Historical Immutability:** Historical rewards are never recalculated under a newer formula version.
3. **Explicit Version References:** Every reward decision and event payload MUST reference the active protocol version used.
4. **Immutable Evidence Binding:** Every reward decision MUST reference immutable evidence artifacts and a 40-character commit SHA (`target_sha == observed_sha`), verified to exist in repository history.
5. **Deterministic Settlement IDs:** Settlement IDs are computed via SHA-256 over protocol version, mission ID, target SHA, outcome type, primary actor, and evidence digest.
6. **Anti-Duplication (Idempotency):** Re-submitting duplicate evidence yields the existing settlement receipt without double-minting points or XP.
7. **No Direct C2 Minting:** C2 may request adjudication for evidence packets; C2 cannot directly assign or mint Points or XP.
8. **No Direct Model Minting:** External AI models (ChatGPT, Jules, Gemini) cannot directly assign or mint Points or XP.
9. **Structured Evidence Primacy:** Human-readable text or agent assertions cannot override structured SEP/1 evidence verification status.
10. **Governed Formula Promotion:** Formula, multiplier, or base value changes require governed protocol promotion to a new protocol version (`SAGE-RP-1.1` or `SAGE-RP-2.0`).

---

## 2. Locked Scoring Constitution (`SAGE-RP-1.0`)

### Base Event Values

| Event Type | Base Point Value |
| :--- | :---: |
| `RECON` | 5 |
| `ANALYSIS` | 10 |
| `BUILD` | 25 |
| `REPAIR` | 25 |
| `VERIFICATION` | 10 |
| `BREAKTHROUGH` | 50 |
| `CAPABILITY_CAPTURE` | 100 |
| `BOSS_KILL` | 100 |
| `BOSS_CAPTURE` | 100 |
| `COLLABORATION` | 10 |
| `REUSE` | 50 |
| `RECOVERY` | 25 |

### Bounded Multiplier Formula

$$\text{Multiplier} = \frac{\text{Difficulty} + \text{Verification Quality} + \text{Impact} + \text{Reuse}}{4}$$

Where each dimension is integer-bounded in $[1, 5]$. Outcome point pool is given by:

$$\text{Outcome Point Pool} = \max(1, \text{round}(\text{Base Points} \times \text{Multiplier}))$$

### Career XP Conversion

$$\text{Career XP} = \lfloor \frac{\text{Cumulative Station Verified Points}}{10} \rfloor$$

XP is minted only for newly earned whole points. Remaining point fractions accumulate in the canonical ledger.

---

## 3. Separation of Outcome Ledger and Contribution Ledger

`SAGE-RP-1.0` decouples outcome classification from participant attribution:

- **Outcome Ledger:** Determines what occurred (e.g., `BOSS_KILL`, verified, point pool = 100).
- **Contribution Ledger:** Determines demonstrable multi-agent contributions toward that outcome.

```json
{
  "contributions": [
    {
      "actor": "CHATGPT_C2",
      "role": "MISSION_CONTROL",
      "contribution_type": "TARGET_IDENTIFICATION_AND_REPAIR_DIRECTION",
      "share_weight": 0.5,
      "claim_ref": "BOSS-0001:c2"
    },
    {
      "actor": "JULES",
      "role": "EXECUTION_BUILDER",
      "contribution_type": "IMPLEMENTATION_AND_TEST_HARNESS",
      "share_weight": 0.3,
      "claim_ref": "BOSS-0001:jules"
    },
    {
      "actor": "GEMINI",
      "role": "RECON_PROBE",
      "contribution_type": "ADVERSARIAL_RECONNAISSANCE",
      "share_weight": 0.2,
      "claim_ref": "BOSS-0001:gemini"
    }
  ]
}
```

### Conservation Principle

$$\sum_{\text{participants}} \text{Attributed Points} = \text{Outcome Point Pool}$$

If evidence or weights are absent/indeterminate, the engine marks `attribution_status = "ATTRIBUTION_INDETERMINATE"` and assigns $100\%$ of the point pool to the primary actor rather than fabricating arbitrary splits.

---

## 4. Automatic C2 Feedback & SAGI Brain Learning Loop

Every settlement produces a formatted `SAGE REWARD RECEIPT` header for C2 HUDs:

```
╔════════════════════════════════════╗
║ SAGE REWARD RECEIPT                ║
╠════════════════════════════════════╣
║ Mission: BOSS-0001                  ║
║ Outcome: BOSS_KILL                  ║
║ Protocol: SAGE-RP-1.0               ║
║                                    ║
║ Verified Points: 100               ║
║ XP Minted: 5                       ║
║ Badge: NONE                        ║
║ Rank: CQL-4                        ║
║                                    ║
║ Evidence: VERIFIED                 ║
║ Settlement: settlement:beb3e9048c7 ║
╚════════════════════════════════════╝
```

The adjudicator automatically emits a `SAGI Learning Signal` payload feeding SAGI Brain's metacognitive and counterfactual learning engine:

```json
{
  "learning_signal_id": "sagi-sig:...",
  "settlement_id": "settlement:...",
  "mission_id": "BOSS-0001",
  "outcome_type": "BOSS_KILL",
  "outcome_point_pool": 100,
  "attribution_status": "VERIFIED_ATTRIBUTION",
  "xp_minted": 5,
  "conservation_verified": true,
  "metacognitive_feedback": {
    "performance_tier": "ELITE",
    "attribution_quality": "VERIFIED_ATTRIBUTION",
    "multi_agent_collaboration": true
  }
}
```

---

## 5. Implementation Anchors

- Protocol & Adjudicator: `sage/experimental/airspace/reward_protocol.py`
- C2 Request Bridge: `sage/c2/reward_adjudication_bridge.py`
- Event Ledger & Persistence: `sage/experimental/airspace/manager.py` & `sage/experimental/airspace/points_xp_economy.py`
- Boss Progression: `sage/experimental/airspace/boss_progression.py`
- Verification Suite: `tests/experimental/test_reward_protocol.py`
- Execution Script: `scripts/execute_boss_fight_adjudication.py`
