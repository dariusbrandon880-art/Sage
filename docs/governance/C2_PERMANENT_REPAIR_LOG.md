# C2 Permanent Repair Log

**Status:** Governing repair-history ledger
**Authority:** Repository implementation truth and validated SAGE governance
**Owner:** `[SAGE::C2::CHATGPT]`

## Purpose

Every consequential repair is permanently logged so future C2 sessions and Big Jump Waves can reuse prior failure analysis instead of rediscovering the same defect.

This is a repair-history ledger, not a second source of truth. Code, tests, validated evidence, and canonical project state remain authoritative.

## Required repair record

Every consequential repair must record:

- **Issue / PR:** stable GitHub reference
- **Detection:** exact failure, symptom, or adversarial finding
- **Root cause:** technical cause, not the surface symptom
- **Affected boundary:** component, interface, or trust boundary
- **Repair:** exact implementation change
- **Why this repair:** why the fix preserves or strengthens governance
- **Regression proof:** tests added/updated and result
- **Evidence:** exact commit SHA / workflow evidence when available
- **Verification:** exact remote HEAD and CI result when available
- **Reusable invariant:** rule future waves must preserve
- **Follow-on risk:** known remaining limitation or next attack surface
- **Search/research input:** external findings used to challenge or strengthen the repair, clearly marked non-canonical

## Permanent repair workflow

**SENSE → RECON → ROOT-CAUSE → REPAIR → REGRESSION → FULL VERIFY → EXACT-SHA RECONCILIATION → LOG → COMPOUND**

A repair is not considered historically complete until the learning is logged alongside its implementation/evidence trail.

## Mandatory pre-repair questions

1. Has this failure class happened before?
2. Which prior repair pattern applies?
3. Does the proposed fix strengthen the canonical boundary or weaken it?
4. Can the fix introduce a new compatibility seam or bypass?
5. What regression test prevents recurrence?
6. What evidence proves the repair landed on the intended SHA?
7. What new invariant should future waves inherit?

## Mandatory post-repair questions

1. What actually failed?
2. Why did the existing controls miss it?
3. What changed?
4. What test now catches it?
5. What adjacent bypass should be attacked next?
6. What should C2/Jules do differently next time?

## Historical index

See `docs/governance/C2_HISTORICAL_REPAIR_AND_RUNTIME_GOVERNANCE.md` for the consolidated historical failure → repair patterns.

## Repair entries

### Template

```text
## [DATE] — [SHORT FAILURE CLASS]

Issue / PR:
Detection:
Root cause:
Affected boundary:
Repair:
Why this repair:
Regression proof:
Evidence:
Verification:
Reusable invariant:
Follow-on risk:
Search/research input:
```

## Operating rule

**No consequential repair disappears into chat.**

The conversation may discover, coordinate, and explain the repair. The repository must retain the durable learning needed to reproduce, verify, and improve the repair in future sessions.
