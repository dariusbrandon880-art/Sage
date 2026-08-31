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

**SENSE → RECON → ROOT-CAUSE → ATTACK → REPAIR → REGRESSION → FULL VERIFY → EXACT-SHA RECONCILIATION → LOG → COMPOUND → NEXT ATTACK**

A repair is not considered historically complete until the learning is logged alongside its implementation/evidence trail.

## Repair-method learning doctrine

The durable learning unit is not only the bug or the patch. It is the **verified repair method** that can be reused against the next failure class.

Every consequential repair should therefore extract:

`FAILURE → SIGNAL → ROOT CAUSE → ATTACK VECTOR → DECISIVE REPAIR → PROOF QUALITY → REGRESSION → EVIDENCE → INVARIANT → REUSABLE REPAIR PATTERN → NEXT ATTACK`

Reusable patterns should teach future C2/engineering work how to recognize and attack a failure, including:

- start from live repository truth rather than a completion narrative;
- retrieve prior repair history before designing a new repair;
- attack the proof itself for vacuous or non-binding assertions;
- require precondition → attempted violation → rejection → unchanged postcondition;
- repair the canonical enforcement boundary instead of weakening a governor or patching a presentation symptom;
- reconcile code, evidence, and exact SHA before promotion;
- preserve rejected paths, near misses, and blocked transitions as negative evidence;
- turn every newly exposed seam into the next bounded attack surface.

Repair learning is **candidate knowledge until validated**. It cannot grant authority, change canonical state, or authorize promotion merely because a model or agent recorded it.

## Autonomous repair-learning operating pattern

When a consequential repair completes, the existing SAGE process should consume the result through the normal validation/archive pathway:

`OBSERVE → RETRIEVE PRIOR REPAIRS → FORM REPAIR HYPOTHESIS → ATTACK → REPAIR → VERIFY → EXTRACT PATTERN → VALIDATE LEARNING → ARCHIVE → REUSE`

The learning mechanism itself is governed. It is not a second control plane and cannot self-promote its own conclusions.

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
3. What attack exposed it?
4. What changed?
5. What test now catches it?
6. What evidence proves the repair?
7. What reusable repair pattern was learned?
8. What adjacent bypass should be attacked next?
9. What should C2/Jules do differently next time?

## Historical index

See `docs/governance/C2_HISTORICAL_REPAIR_AND_RUNTIME_GOVERNANCE.md` for the consolidated historical failure → repair patterns.

## Repair entries

## 2026-08-30 — Self-Owned Interface Identity Convention & Google Station Boundary

**Issue / PR:** Google Station Self-Owned Nameplate Hardening

**Detection:** Architectural audit of station identity handling revealed that Google/Gemini responses relied on caller or ChatGPT-supplied station tags rather than generating self-owned nameplates (`[SAGE::C2::GOOGLE]`) from governed session state at the interface boundary.

**Root cause:** Station identity was defined primarily as an external capability label (`[SAGE::INTEL::GEMINI]`) rather than a self-owned runtime builder boundary (`[SAGE::C2::GOOGLE]`).

**Affected boundary:** `GeminiInteractionsAdapter` (`sage/runtime/model_adapters.py`), `GeminiJulesClient` (`sage/integration.py`), and `Station` enumeration (`sage/c2/conversation_provenance.py`).

**Repair:** Bound `GeminiInteractionsAdapter` and `GeminiJulesClient` to station `[SAGE::C2::GOOGLE]`, enforcing self-owned nameplate generation at session start and failing closed if a caller attempts to spoof ChatGPT (`[SAGE::C2::CHATGPT]`) or supply a synthetic identity. Added unit tests in `tests/c2/test_google_interface_identity.py`.

**Why this repair:** Enforces the core invariant that interface station tags must be self-owned projections from governed runtime session identity; no caller or model can manufacture authority or spoof another station.

**Regression proof:** 3/3 tests passing in `tests/c2/test_google_interface_identity.py`.

**Evidence:** SHA `9e2e5dd44b03a2b935a962882a7343d0bc568a19`.

**Verification:** Local pytest run verified 0 regressions across C2 and runtime suites.

**Reusable invariant:** Every interface station emits its own self-owned nameplate from governed runtime identity; station identity selects role and policy context, never C2 authority.

**Follow-on risk:** Audit all remaining client adapters to ensure every agent station emits self-owned nameplates at session start.

**Search/research input:** Internal C2 station identity directive.

## 2026-08-30 — Live Capability Execution Non-Empty Capability ID Enforcement

**Issue / PR:** Live Capability Boundary Wave

**Detection:** Code review of `execute_live_capability` in `sage/c2/live_operation_receipt.py` revealed that capability instances with an empty or whitespace-only `capability_id` attribute were accepted, generating unanchored operation receipts.

**Root cause:** Boundary check only validated `target_resource` presence, missing an explicit validation check on `capability.capability_id`.

**Affected boundary:** Live Operation Receipt Boundary (`sage/c2/live_operation_receipt.py`).

**Repair:** Enforced explicit `capability_id` validation in `execute_live_capability` (`capability_id = str(getattr(capability, "capability_id", "")).strip()`). If empty, raises `ValueError`. Added unit tests in `tests/c2/test_live_capability_boundary_hardening.py`.

**Why this repair:** Prevents anonymous capability invocation and ensures every cryptographic receipt is tied to a verified capability identity.

**Regression proof:** 3/3 tests passing in `tests/c2/test_live_capability_boundary_hardening.py`.

**Evidence:** SHA `9e2e5dd44b03a2b935a962882a7343d0bc568a19`.

**Verification:** Local pytest run verified 0 regressions.

**Reusable invariant:** Every live capability receipt must cryptographically bind a non-empty `capability_id` and non-empty `target_resource`.

**Follow-on risk:** Audit all live capability provider implementations to ensure non-empty `capability_id` attributes are assigned at instantiation.

**Search/research input:** Internal C2 boundary audit directive.

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

## 2026-08-30 — Unified Agent Runtime Context Drift

**Issue / PR:** Big Jump Wave `feat/c2-unified-agent-control-plane-wave`

**Detection:** Live repo reconciliation showed the merged transition hardening was present, but the model-facing runtime still returned model responses without binding station identity, pinned policy context, or provenance digest. Gemini transport also lacked the same `SAGEProtocolGovernor` output validation already applied to OpenAI.

**Root cause:** Governance had been strengthened at the capability transition boundary without fully propagating the same identity/context contract through every model adapter. This created a cross-agent and policy-context seam between transport and runtime reconciliation.

**Affected boundary:** Model adapter → SAGE runtime envelope → protocol governor → response reconciliation; specifically Gemini and cross-station response paths.

**Repair:** Added immutable `agent_identity`, `policy_digest`, and `provenance_digest` to `SAGERuntimeEnvelope`; bound those values to canonical state and station/model-role/policy context; added corresponding fields to `ModelResponse`; required governed adapters to declare a station; strengthened `SAGERuntime.reconcile()` with station, policy, policy-digest, provenance, and structured-response identity checks; and routed Gemini output through `SAGEProtocolGovernor` before returning a response.

**Why this repair:** It strengthens the existing SAGE runtime control plane rather than creating a second authorization framework. Model outputs remain proposals/evidence only; the runtime owns identity and governance context.

**Regression proof:** Expanded `tests/runtime/test_model_gateway.py` for station, policy-context, provenance, and state-drift rejection. Expanded `tests/runtime/test_model_adapters.py` for Gemini governance and forged cross-station output rejection. Full-suite execution remains a promotion gate until remote CI observes this branch.

**Evidence:** Implementation commits on branch `feat/c2-unified-agent-control-plane-wave`: `fac0b548f183a73fe40d364a73d2b9f07f3e529e`, `07c4cdc59ba73f56af03ba267492f492eb37c33b`, `20b18bc6b07660c19d128a672748923887bd651f`, `31d2a888c2feca0dd08ec7c46f1c31704d2f5678`.

**Verification:** Branch-level code has been reconciled through GitHub. Local/full test execution and exact-head CI remain required before promotion; no green result is claimed here.

**Reusable invariant:** Every governed model response must carry and reconcile the exact station identity, canonical state digest, pinned policy context, and provenance context that were supplied to the adapter. A model cannot redefine any of them.

**Follow-on risk:** Extend the same contract to every direct runtime/tool/CLI entry point and verify that legacy `ChatGPTClient` execution cannot bypass `render_governed_chatgpt_turn`.

**Search/research input:** NIST's 2026 agent identity/authorization work emphasizes explicit identification, authorization, auditing, non-repudiation, and prompt-injection controls. Microsoft's current agent-governance work independently emphasizes session policy pinning, fail-closed evaluation, complete snapshots, and action-bound execution-time revalidation. These are external threat-model inputs, not SAGE canonical authority.

## 2026-08-30 — Repair-Method Learning / Proof-Attack Discipline

**Issue / PR:** Big Jump Wave `feat/c2-autonomous-repair-learning-wave`

**Detection:** C2 observed that a successful repair could remain isolated as a one-off implementation lesson even when the repair process itself contained reusable reconnaissance, falsification, proof-attack, and reconciliation techniques.

**Root cause:** Existing repair records preserved failure and implementation history, but did not explicitly require extraction of the **repair method** as reusable candidate knowledge for future waves.

**Affected boundary:** C2 repair workflow → historical learning → future Big Jump reconnaissance and verification.

**Repair:** Extended the Big Jump protocol and Full Organism Consumption pathway to treat verified repair methods as reusable learning; added explicit `FAILURE → SIGNAL → ROOT CAUSE → ATTACK → REPAIR → PROOF → REGRESSION → EVIDENCE → INVARIANT → REUSABLE PATTERN → NEXT ATTACK` extraction; required proof-quality review and exact-SHA reconciliation; and made clear that repair learning remains subordinate to canonical governance and validation.

**Why this repair:** It compounds the execution capability of SAGE without introducing a parallel authority system. Future waves can retrieve validated repair patterns before designing the next repair.

**Regression proof:** Governance pathway documents now explicitly require historical repair retrieval, attack-the-proof discipline, precondition/violation/rejection/unchanged-postcondition testing, exact-SHA reconciliation, and permanent learning.

**Evidence:** Wave branch commits `c86ad6f26a3226a1cfbe3bb65a46432f32d91663` and `1f4da80059c8bbd5b582b5694c6949bc617ac773`.

**Verification:** Repository documents were written against the reconciled `main` baseline `35cf2717f881e1530c60fb98d6d0549962503dca` on the dedicated wave branch. Runtime/test execution is not claimed from documentation-only changes; promotion remains subject to the repository's normal CI and review gates.

**Reusable invariant:** A consequential repair is incomplete as organism learning until the verified repair method, proof-quality lesson, invariant, and next attack surface are durable and reusable.

**Follow-on risk:** Implement machine-readable retrieval/validation of repair patterns only if an existing canonical learning/archive path can be strengthened; do not create a second repair authority.

**Search/research input:** The wave was primarily driven by repository-native repair history and observed C2 execution patterns. External research remains a falsification input and cannot promote repair learning into canonical authority.

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
