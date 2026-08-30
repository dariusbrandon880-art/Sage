# C2 Historical Repair & Runtime Governance Guide

**Status:** Governing repair-pattern reference / reusable hardening guidance
**Authority:** Git/main implementation truth + validated SAGE governance; external research is supporting evidence only
**Primary station:** `[SAGE::C2::CHATGPT]`

## Purpose

This document turns recurring C2 failures into reusable engineering checks. It is intended to be consulted during every consequential Big Jump Wave, runtime-boundary hardening pass, and regression repair so known failure classes are attacked before they are rediscovered.

The guide is not a second authority system. It is a durable index of validated repair patterns and adversarial questions. Canonical implementation and validated project state remain authoritative.

## Core runtime principle

The model is a proposer; the governed runtime is the authority boundary.

Use this chain for consequential model/runtime behavior:

**REHYDRATE → REALITY LOCK → IDENTITY LOCK → ACTIVE-FRONTIER LOCK → GOVERN → PROPOSE → VERIFY → AUTHORIZE → EXECUTE → OBSERVE → EVIDENCE → VALIDATE → PROMOTE → PROJECT**

Never collapse these states:

- execution != evidence
- evidence != verification
- verification != validation
- validation != authorization
- authorization != promotion
- presentation != authority
- model output != canonical state
- passing tests != demonstrated capability

## Historical failure → repair patterns

### 1. GPT/SAGE runtime boundary

**Failure:** Hardened ChatGPT boundary required `frontier/gate/next_move`; legacy callers supplied an older context shape.

**Repair:** Compatibility adapter rehydrates missing presentation fields from canonical runtime status/current objective/task. Explicit C2 fields remain authoritative. The direct boundary remains fail-closed.

**Invariant:** Compatibility adapters translate canonical state; they never invent authority or weaken the boundary.

**Reference:** PR #338 / Issue #340.

### 2. Synthetic immersion state

**Failure:** ChatGPT integration constructed synthetic `ImmersionState` values instead of consuming canonical state.

**Repair:** Remove hard-coded flight/phase/authority state; rehydrate canonical `ImmersionState` and route through the existing runtime/projection boundary. Fail closed when unavailable.

**Invariant:** Presentation is a read-only projection of canonical state.

**Reference:** PR #339 repair history.

### 3. Model-output contract overconstraint

**Failure:** OpenAI/model adapter required structured reasoning/proposed-action payloads even for ordinary read-only/status responses that did not provide them.

**Repair:** Trace the canonical ModelAdapter → SAGERuntime → governor → ChatGPT boundary and repair the real contract seam without weakening governance.

**Invariant:** Fix compatibility at the adapter boundary; never relax the canonical safety contract merely to satisfy an older caller.

**Reference:** PR #337.

### 4. Experiment receipt self-promotion

**Failure:** `record_flight_receipt()` treated `PASS + evidence exists` as `PROMOTED`.

**Repair:** Receipt recording leaves `ValidationStatus.HOLD` until independent validation and authorization occur.

**Invariant:** **EXECUTION → EVIDENCE → VERIFY → VALIDATE → AUTHORIZATION → PROMOTE.**

**Reference:** PR #331.

### 5. Silent governance/evidence failure

**Failure:** Big Jump Wave swallowed ledger exceptions with `except Exception: pass`.

**Repair:** Propagate ledger failures into flight failure/reconciliation and add regression coverage.

**Invariant:** Trust/evidence bridge failures cannot disappear.

**Reference:** PR #331.

### 6. Synthetic Five-Flight PASS receipts

**Failure:** Duplicate dispatcher manufactured PASS receipts instead of deriving them from actual execution.

**Repair:** Replace duplicate implementation with an adapter over the canonical `BuildJumpWaveEngine`; receipts derive from actual execution summaries and exact-head provenance.

**Invariant:** Evidence must be causally attributable to real execution.

**Reference:** PR #294.

### 7. SHA/provenance drift

**Failure:** Evidence was bound to base/main or an earlier execution SHA instead of the submitted PR HEAD.

**Repair:** Freeze the exact execution HEAD, rerun only invalidated evidence from that checkout, bind `exact_git_head/executed_head`, and verify remote HEAD == tested/evidenced HEAD.

**Invariant:** No promotion from evidence whose implementation identity cannot be reconciled.

**References:** PRs #304, #306, #316, #305/#312.

### 8. Stale branch / duplicate architecture

**Failure:** PRs accumulated already-merged or cross-frontier work and became large/non-mergeable.

**Repair:** Rehydrate current main; classify KEEP/DROP/REPAIR; preserve unique additive capability; remove duplicate/stale evidence; reconcile before verification.

**Invariant:** Current repository truth precedes branch narrative.

**References:** PRs #299, #315, #316.

### 9. Git conflict-marker evidence contamination

**Failure:** Historical evidence files contained committed merge-conflict markers.

**Repair:** Remove only the contaminating markers, preserve validated evidence, reconcile the branch graph, and rerun affected verification.

**Invariant:** Evidence integrity is itself a verification gate.

**Reference:** PR #316.

### 10. Operator acceptance manufactured from CI

**Failure:** Deterministic CI/synthetic evidence could produce customer-facing `ACCEPTED`.

**Repair:** Require per-interface PASS plus attributable evidence. Engineering PASS remains distinct from empirical/operator ACCEPTED. Fail closed on partial or missing evidence.

**Invariant:** CI proves engineering conditions; it does not manufacture real-world acceptance.

**References:** #286, #288, #293, #298.

### 11. Static session manifest masquerading as live state

**Failure:** Committed manifest schema contained stale or empty runtime state.

**Repair:** Materialize `.sage/session_manifest.json` atomically from live HEAD and required interfaces before verification; verify populated values and exact SHA.

**Invariant:** Session continuity is rehydrated from live canonical state, not static chat assumptions.

**Reference:** PR #289.

### 12. Mission drift / chat-derived authority

**Failure:** Caller-supplied or conversational mission state could displace canonical mission hierarchy.

**Repair:** Canonical G1-G8 hierarchy + repo-first rehydration + fail-closed bootstrap validation + anti-drift contract.

**Invariant:** Conversation is a control surface, not the system of record.

**References:** #291, #292, #322.

### 13. Sports temporal/provenance fabrication

**Failure:** Backdated observations, fabricated market/consensus data, synthetic outcomes, or invalid CLV.

**Repair:** Reject already-started events; capture real timestamps/source hashes; unresolved outcomes remain `PENDING`; CLV is `N/A` without a real close; enforce chronological OOS + Brier/log-loss/calibration/baseline gates.

**Invariant:** Temporal and source provenance are part of the evidence contract.

**Reference:** PR #315 repair history / Issue #156.

### 14. Evidence-only Big Jump mistaken for capability gain

**Failure:** A wave receipt and full tests were reported as new capability when target files were unchanged from main.

**Repair:** Require a concrete net code/behavior delta per flight. Evidence-only execution does not count as advancement.

**Invariant:** A successful workflow is not itself a capability delta.

**Reference:** PR #310.

### 15. Flight collision / parallel duplication

**Failure:** Parallel sessions could target overlapping namespaces or capabilities.

**Repair:** Collision locks + explicit target/collision zones + replacement of already-claimed targets with the next uncovered high-leverage work.

**Invariant:** Parallelism changes scheduling, not ownership boundaries.

**References:** PRs #305/#316 and Big Jump governance.

## Adversarial checklist for every Big Jump Wave

Before promotion, explicitly attack these questions:

1. Can a receipt self-promote?
2. Can model output mutate canonical state?
3. Can presentation manufacture progression?
4. Can a legacy adapter bypass the new boundary?
5. Can missing state be silently substituted with synthetic defaults?
6. Can stale authorization survive a state change?
7. Can evidence be attributed to the wrong SHA?
8. Can a failed trust/evidence bridge disappear?
9. Can CI success be mistaken for real-world acceptance?
10. Can a wave report capability without a concrete behavior delta?
11. Can parallel flights collide or duplicate work?
12. Can chat memory override repository/master-archive truth?

Any **yes** is a repair target, not a reason to weaken the gate.

## External research synthesis — supporting evidence

Current 2026 agent-governance research independently converges on several principles already present in SAGE:

- Runtime governance belongs at action/intervention boundaries rather than solely in prompts.
- Model outputs should remain untrusted proposals until mediated by trusted runtime code.
- Runtime policy evaluation should be deterministic where possible and fail closed on validation/dispatch errors.
- Complete host-supplied snapshots/provenance are necessary; stale authorization is a distinct stateful-governance risk.
- Authorization should be rechecked against current policy/state immediately before consequential effects.
- The host/runtime integration is part of the trusted computing base; an uninstrumented path is outside the guarantee.

Supporting references include Microsoft's Agent Control Specification/security model, recent runtime-governance research on trusted provenance and fail-closed execution, and recent work on stale authorization in stateful agent systems.

External research is **not canonical SAGE authority**. It is used to challenge, strengthen, and falsify SAGE assumptions; validated SAGE implementation remains the source of truth.

## Permanent repair loop

**REHYDRATE → REALITY LOCK → FIND BYPASS → REPAIR ROOT CAUSE → ADD ADVERSARIAL REGRESSION → RUN FULL SUITE → VERIFY EXACT REMOTE SHA → RECONCILE → PROMOTE ONLY WHEN THE EVIDENCE CHAIN IS COMPLETE.**

## Meta-lesson

When a hardened boundary breaks an older caller, do not weaken the boundary. Repair the compatibility seam from canonical state.

When a receipt claims success, ask exactly which state it proves: execution, evidence, verification, validation, authorization, or promotion.

When a branch reports completion, compare it with current main and the exact remote HEAD before trusting the report.

When a wave produces receipts but no concrete capability delta, classify it as execution/evidence work rather than capability advancement.

When external research agrees with SAGE, record it as supporting evidence—not authority. When it conflicts with SAGE, use the conflict to trigger falsification and architectural review.
