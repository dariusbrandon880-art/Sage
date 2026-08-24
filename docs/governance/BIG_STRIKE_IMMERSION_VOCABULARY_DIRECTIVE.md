# SAGE BIG STRIKE CAMPAIGN & IMMERSION VOCABULARY DIRECTIVE

**Status:** Governed Immersion Vocabulary & Milestone Campaign Specification
**Authority:** SAGE C2 Persistent Operating Contract
**Invariant:** Simulation/Game Operations Vocabulary Only — Zero Real-World Kinetic/Wagering Mechanics

---

## Executive Objective

Formalize the "Big Strike" campaign milestone architecture and SAGE Immersion Vocabulary Layer, connecting major capability jumps to persistent fleet progression, qualification levels (CQL/SQL), and After Action Reports (Evidence Receipts).

---

# 1. CAMPAIGN MILESTONE HIERARCHY

```text
SAGE CAMPAIGN LAYER

Campaign
   └── Big Strike (Major Verified Strategic Capability Jump)
        └── Flight (Parallel Capability Vector)
             └── Sortie (Governed Mission Execution Unit)
                  └── Evidence Receipt (Proof of Achievement)
                       └── XP Award (Verified Growth)
```

- **Sortie**: Individual governed operation.
- **Flight**: Grouped parallel execution vector (F1–F5).
- **Big Strike**: Strategic campaign milestone representing a major verified capability jump across multiple validated flights (e.g. *Big Strike: Frontier Intelligence Expansion*).

---

# 2. IMMERSION VOCABULARY MAPPING

| Immersion Operation Term | SAGE Governed Equivalent | Input & Verification Requirement |
| ------------------------ | ------------------------ | ------------------------------- |
| **Precision Strike** | Targeted Capability Upgrade | Bounded code delta with 100% test pass proof. |
| **Recon Strike** | Intelligence Discovery Mission | Read-only repository audit & threat model recon. |
| **Defense Strike** | Security Hardening Mission | Codeowners, secret scanning, & vulnerability patching. |
| **Countermeasure Sweep** | Adversarial Testing Flight | Failure injection & fail-closed boundary verification. |
| **Supply Drop** | Evidence Delivery | Cryptographically signed receipt or artifact manifest. |
| **Command Push** | Approved Deployment | Authorized release or promotion to Master Archive. |
| **After Action Report** | Evidence Receipt | SHA-256 evidence manifest stored in `evidence_capture/`. |

---

# 3. FLEET COMMAND HUD & QUALIFICATION BINDING

```text
============================================================
                     SAGE FLEET COMMAND HUD
============================================================
Operator Call Sign: Human Director (CQL-7 / SQL-7)
C2 Command:        Level 4 (C2 Synthesis & Governance)
Jules Wing:        Level 4 (Engineering Execution & Build Verification)
Intel Squadron:    Level 3 (Recon & Adversarial Telemetry)

ACTIVE CAMPAIGN:
  [Big Strike 001] — Frontier Intelligence & Public Posture Hardening
  Status: CLEARED / VERIFIED
  AAR Receipt: receipt_c2_post_merge_validation_2026_08_23

QUALIFICATION PROMOTION GATE:
  ✓ Test Evidence (870/870 PASS)
  ✓ Security Clearance (CODEOWNERS & Secret Scan Clean)
  ✓ Capability Receipt (Signed SHA-256 Digest)
  ✓ Adversarial Survival (Failure Injection Passed)
============================================================
```

---

# 4. HARD GOVERNANCE LAWS

1. **Evidence-Driven Promotion Only**: Rank and qualification levels increase strictly upon verified evidence receipts (`verified_event_ref`). Zero XP or rank advancement awarded for raw activity or unverified chat turns.
2. **Zero Fictional Capability**: Presentation layers (HUDs, logs, summaries) must never display or pretend capabilities exist that are not verified in code and tests.
3. **Simulation Boundary**: All "strike" operations represent software execution and verification units within the SAGE runtime. Real-world kinetic, destructive, or monetary mechanics are strictly prohibited.
