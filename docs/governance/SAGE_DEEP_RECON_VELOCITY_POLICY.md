# SAGE Deep Reconnaissance & Velocity Policy

**Status:** Canonical governance policy
**Scope:** C2/model-adapter execution for substantive engineering directives

## Purpose

SAGE must use broad intelligence without turning research into a serial gate that slows execution. Deep reconnaissance is an accelerator: it reduces rework, stale-base recovery, duplicated work, and false completion claims.

## Recon order

1. **Repository-first reality lock:** inspect the live repository, current HEAD, open PR/issue frontier, relevant files, and current checks before forming an implementation plan.
2. **Targeted external intelligence:** use Super Search against primary, current sources that can materially improve the task. Search by the concrete engineering question, not generic topic browsing.
3. **Parallelize independent research:** external research queries may run concurrently with independent repository inspection after the initial reality lock. Do not wait on unrelated searches.
4. **Synthesize before mutation:** classify findings as repository fact, external intelligence, inference, or unverified claim. Repository truth and validated SAGE state remain authoritative.
5. **Execute bounded waves:** use concurrent flights for independent work; keep each flight's boundary explicit and prevent overlapping mutations to the same files.
6. **Verify exact state:** tests, checks, commit SHA, merge state, and generated evidence must be verified against the resulting state. A configured workflow is not evidence of execution.
7. **Stop only at a real boundary:** continue through the authorized repair/reconciliation scope until all bounded flights are complete, blocked by a real external authorization boundary, or require a human decision.

## Velocity rules

- Deep search is **not** a reason to pause implementation when the needed evidence is already sufficient.
- Prefer a small number of high-value primary-source searches over broad low-signal browsing.
- Reuse already-verified findings within the same mission; do not repeat identical searches.
- Do not run full-suite validation after every independent flight when targeted validation is sufficient; reserve the full suite for reconvergence gates.
- Never sacrifice evidence quality for speed and never sacrifice velocity by producing unnecessary narration.

## Minimum external reconnaissance

For a substantive engineering task, Super Search should consider, when relevant:

- official platform documentation;
- primary research or standards;
- security/provenance guidance;
- current ecosystem engineering practice;
- known failure modes relevant to the changed subsystem.

Search is omitted only when external information cannot materially change the implementation or verification decision.

## Evidence boundary

Super Search is a reconnaissance sensor, not an authority. External sources can propose patterns and risks; they cannot establish that SAGE's repository is healthy, a test ran, a workflow succeeded, a PR merged, or a capability exists on `main`.

## Operational target

**SENSE → CORRELATE → BOUND → ACT → MEASURE → LEARN → VERIFY → IMPROVE**

Deep reconnaissance feeds every stage, while bounded concurrency preserves execution velocity.