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

## 2026-08-30 — Unified Agent Control Plane Boundary

**Issue / PR:** Big Jump Wave from substrate `6e80b642c24782f3421ceee017aa19eb05f559b9`.

**Detection:** Repository recon found provider asymmetry: OpenAI output passed through `SAGEProtocolGovernor`, while Gemini returned model output after citation extraction. Agent task input validation also accepted operational context without requiring canonical, verified immersion state.

**Root cause:** Governance existed at individual adapter seams instead of being uniformly enforced at the shared model/runtime and agent-task boundaries.

**Affected boundary:** Agent identity → runtime envelope → model adapter → protocol governor → agent task contract → state transition boundary.

**Repair:** Routed Gemini output through the same `SAGEProtocolGovernor`; bound accepted `ModelResponse` values to station, policy version/digest, and provenance digest; strengthened `AgentExecutionContract` with canonical `ImmersionState`, verified trust, provenance, agent identity, objective identity, and permission-boundary identity checks.

**Why this repair:** Agent role remains contextual policy input, never authority. Every provider uses the same runtime/governor path and state-changing execution remains downstream of explicit authorization controls.

**Regression proof:** Added shared adapter governance tests covering Gemini station spoofing and model authority claims, plus task-contract adversarial tests for forged/unverified state, missing provenance, agent identity mismatch, and cross-bound permission boundaries. Local results are recorded only when actually executed; repository commits do not substitute for execution evidence.

**Evidence:** Unified repair branch begins at exact substrate `6e80b642c24782f3421ceee017aa19eb05f559b9`; implementation sequence currently reaches `77b656041007352a29b50a554d9c263079d1174f`.

**Verification:** Remote exact-head CI is not yet green for this branch. Promotion remains HOLD until focused tests, full platform tests, pre-commit, exact-head CI, and SHA reconciliation are completed.

**Reusable invariant:** Every governed agent enters the same canonical control plane; agent identity selects role and policy context, never an alternate authority path.

**Follow-on risk:** Direct CLI/tool/runtime entry points, authorization artifact provenance, concurrent authorization consumption, and alternate promotion/evolution routes require dedicated adversarial coverage.

**Search/research input:** External governance research may inform threat models, but repository truth and validated tests remain canonical.

## 2026-08-30 — Legacy ChatGPT Boundary Compatibility Seam

**Issue / PR:** PR #338 / Issue #340

**Detection:** Exact-head CI on the hardened GPT/SAGE runtime boundary produced six regressions in legacy ChatGPT, continuity, client, and API integration paths. The hardened boundary correctly required `frontier`, `gate`, and `next_move`, while older callers supplied an incomplete context shape.

**Root cause:** The compatibility seam had not yet translated legacy runtime context into the newer canonical C2 response contract before entering the governed boundary.

**Affected boundary:** Legacy ChatGPT integration → SAGE runtime envelope → governed immersion boundary.

**Repair:** Rehydrate missing presentation fields from canonical runtime status/current objective/task context in the legacy adapter; preserve explicitly supplied C2 fields as authoritative; keep the direct boundary fail-closed. Added a regression proving legacy callers are hydrated without bypassing governance.

**Why this repair:** It strengthens the canonical boundary instead of weakening its contract. Compatibility code translates canonical state; it does not invent authority or relax validation.

**Regression proof:** Added regression coverage for legacy-boundary hydration; prior boundary and runtime tests remained part of the verification surface.

**Evidence:** Repair SHA `07648c5955e292a70a34b79601a75bf56c9b7e9d`; regression SHA `c3cb224fc1bf2bff1b70ef8378b691a937d0ed87`.

**Verification:** Exact-head remote CI remained the next gate after the repair; do not treat the repair commit itself as proof of full-suite/CI completion.

**Reusable invariant:** When hardening breaks an older caller, repair the adapter seam from canonical state; never weaken the hardened governor to preserve legacy behavior.

**Follow-on risk:** Audit every remaining ChatGPT-facing adapter and alternate entry point for equivalent contract-shape drift.

**Search/research input:** External agent-governance research supported runtime-boundary enforcement, fail-closed mediation, and separation of model proposal from trusted runtime authority; external research remains non-canonical.

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