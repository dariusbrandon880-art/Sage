# C2 Marine Execution Mode

## Purpose

**Marine** is an internal shorthand for SAGE's hard-execution operating posture. It is a workflow term, not a product identity, organizational identity, military affiliation, or presentation theme.

## Canonical meaning

When C2 or an operator invokes **Marine Mode**, interpret it as:

> **repo-first recon → bounded execution → verification → evidence → advance**

The mode is deliberately operational and surgical. It does not authorize broader scope, bypass governance, invent state, or replace normal SAGE controls.

## Execution contract

1. **Rehydrate repository truth first.**
   - Read the live repository state, current branch/base/head, relevant governance, active work, open PRs/issues, and applicable evidence.
   - Treat repository state as authoritative over conversational memory, stale summaries, generated projections, and PR descriptions.

2. **Map the active boundary before touching files.**
   - Identify the exact objective, affected paths, dependencies, protected boundaries, concurrent work, and promotion path.
   - Do not collide with an active engineering task or silently absorb another agent's boundary.

3. **Execute the smallest correct change.**
   - Prefer minimum connection over new infrastructure.
   - Preserve existing SAGE architecture, governance, namespaces, provenance, and state semantics.
   - Do not introduce synthetic authority, hidden state, invented APIs, or fallback claims that are not grounded in canonical state.

4. **Verify behavior, not narrative.**
   - Run the narrowest meaningful tests first, then the required broader gates when justified.
   - Distinguish test success from empirical/runtime proof.
   - Preserve negative-path and fail-closed behavior.

5. **Record evidence and Git truth.**
   - Capture exact changed paths, commit SHA, relevant test/workflow results, and promotion state.
   - Never claim execution, success, merge, or deployment without observable evidence.

6. **Advance only through authorized gates.**
   - A green test does not create merge authority.
   - Do not infer broad authorization from a prior approval.
   - Respect Mission Director approval requirements and existing repository governance.

7. **Keep the posture non-theatrical.**
   - Marine does **not** mean Marine Corps branding, military role-play, ceremonial language, or cosplay.
   - Use the term only as an internal shorthand for disciplined, high-tempo repository execution.

## Relationship to SAGE C2

Marine Mode is an **operating posture**, not a new SAGE architecture layer and not a replacement for the Five Flight model.

The normal C2 hierarchy remains authoritative:

**SAGE mission → C2 synthesis/coordination → bounded execution → verification → validated knowledge/state → next frontier**

The Five Flights remain dynamic, reusable execution vehicles. Marine Mode does not assign permanent roles to flights and does not change their ownership or boundaries.

## Anti-drift rules

- No repository evidence → no claim.
- No authorized boundary → no modification.
- No verification → no promotion claim.
- No merge authority → no merge.
- Stale generated state is evidence of a projection defect, not canonical authority.
- Conversation continuity may guide investigation, but durable repository/archive state remains the source of truth.

## Scope

This document defines terminology and operating posture only. It does not grant permissions, alter authentication, modify protected namespaces, or override any existing SAGE governance document.
