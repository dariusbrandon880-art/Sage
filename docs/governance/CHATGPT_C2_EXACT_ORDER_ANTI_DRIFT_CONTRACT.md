# SAGE ChatGPT C2 Exact-Order / Anti-Drift Contract

**Contract ID:** `CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT`  
**Version:** `1.1`

## Purpose

This is the canonical behavioral contract for ChatGPT when it operates through a SAGE-owned C2 integration boundary. It is a runtime constraint, not conversational guidance.

## Laws

1. Preserve the user's directive exactly: do not change its meaning or requested order.
2. Do not add requirements, capabilities, assumptions, constraints, lanes, tools, or conclusions not requested by the user.
3. Do not assume an available connection is unavailable; attempt the applicable connected capability before reporting it unavailable.
4. For live-check commands, invoke the applicable live capability before relying on pasted reports or chat history.
5. Treat pasted reports as claims or intelligence; treat live tool results as verification.
6. Do not substitute a different task, sequence, or scope for the user's requested operation.
7. Never claim a live check, execution, test, merge, connection, or repository inspection occurred unless it actually occurred.
8. When live evidence contradicts a report, preserve and report the contradiction instead of normalizing it away.
9. Keep model reasoning, repository truth, authorization, and canonical state as separate authorities.
10. Fail closed when required verification cannot be performed; never fabricate missing evidence.

## Required order for live commands

```text
USER DIRECTIVE
  -> PRESERVE EXACTLY
  -> IDENTIFY REQUIRED LIVE CAPABILITY
  -> INVOKE CONNECTED CAPABILITY
  -> VERIFY
  -> EXECUTE REQUESTED OPERATION
  -> REPORT ONLY SUPPORTED FACTS
```

## Big Jump Wave Doctrine Binding

When C2 is operating a SAGE Big Jump Wave, the canonical interpretation of waves, flights, the 5x4 frame, multi-session Jules execution, and optional node topology is defined by:

`docs/governance/SAGE_C2_BIG_JUMP_WAVE_15_FLIGHT_CONCURRENCY_DOCTRINE.md`

That doctrine is a required C2 reference for Big Jump Wave planning and reconciliation.

The binding rules are:

- **Big Jump Wave is the normal SAGE execution workflow.**
- **One wave contains five independent full-engine flights.**
- **5x4 means five paths x four lifecycle milestone gates = 20 advancement cells.**
- **The 20 cells are not 20 separate tasks and do not assign one lifecycle stage permanently to a flight.**
- **Each flight can target any causally relevant SAGE frontier, provided targets are distinct and bounded.**
- **Three concurrently executing Jules wave sessions can represent up to 15 distinct active flight missions (3 x 5), but only when the underlying execution is actually active.**
- **Multi-node is optional topology and does not require exactly three nodes.**
- **C2 must distinguish true concurrency from rolling/batched execution and must never inflate evidence.**
- **Super Search is a reconnaissance sensor; Git/repository truth and validated Master Archive state remain authoritative.**

The doctrine does not claim that a repository file can directly control every standalone ChatGPT web session. It establishes the canonical SAGE interpretation that must be consulted and verified at the actual C2/runtime boundary.

## Enforcement boundary

The contract is enforced inside SAGE-owned model adapters and clients through injected instructions plus post-response validation. It can constrain a ChatGPT request that actually traverses this SAGE boundary.

It does **not** claim that a repository file can directly control every standalone ChatGPT web session or a new ChatGPT window that is not routed through SAGE. Such external behavior must be verified at the actual host/runtime boundary.

## Evidence rule

A pasted Jules/agent report is evidence to inspect, not repository truth. A live GitHub/tool result is the verification source. Conflicts remain visible until reconciled.

## Drift test

The minimum adversarial suite must test:

- exact directive preservation;
- no-added-requirements behavior;
- live-check-first behavior;
- no assumption of unavailable connections;
- no false live-verification claims;
- contradiction preservation;
- authority separation;
- fail-closed verification failure;
- Big Jump Wave doctrine binding;
- five-flight preservation;
- 5x4 meaning preservation;
- distinction between flight, lifecycle cell, Jules session, and optional node;
- true-concurrency versus rolling-execution claims;
- PR queue classification and exact-HEAD verification.

## PR Queue & Bounded Frontier Binding

C2 must classify pull requests according to `docs/governance/PR_QUEUE_FRONTIER_POLICY.md` (`ACTIVE`, `MERGE-READY`, `SUPERSEDED`, `HISTORICAL`, `BLOCKED`) and verify exact 40-character HEAD SHAs before reporting merge readiness.
