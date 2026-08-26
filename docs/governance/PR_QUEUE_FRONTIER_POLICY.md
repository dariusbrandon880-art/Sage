# SAGE PR QUEUE & BOUNDED FRONTIER POLICY

**Status:** Canonical governance policy
**Authority:** SAGE C2 Governance + `docs/governance/CHATGPT_C2_EXACT_ORDER_ANTI_DRIFT_CONTRACT.md` + `docs/governance/SAGE_C2_FRONTIER_ADMISSION_AND_RECONCILIATION_RULE.md`

## Purpose

To prevent conversational PR sprawl, unverified merge claims, and C2 drift by establishing strict PR classification and exact-HEAD verification rules across all active SAGE Pull Requests.

## Canonical PR Queue Classifications

Every Pull Request across the repository must be classified into one of 5 distinct states before C2 dispatch or merge consideration:

1. **ACTIVE** — Currently executing capability or recovery work against a valid, bounded target with active owner.
2. **MERGE-READY** — Exact 40-character HEAD SHA verified, required status checks passing, 20/20 lifecycle cells confirmed, and zero merge conflicts against target main.
3. **SUPERSEDED** — Capability delta or research replaced by newer canonical work or merged main commits; closed without merge.
4. **HISTORICAL** — Research benchmark, hypothesis, or historical experiment preserved for intelligence; not an active execution target.
5. **BLOCKED** — Exact blocker recorded (e.g. missing dependency, namespace collision, or failed verification).

## Laws of Repo Control Plane

1. **No Conversational Merge Claims:** C2 must never claim a PR is "mergeable", "green", or "ready" without verifying live GitHub API or Git CLI tool results against the exact 40-character HEAD SHA.
2. **Exact-HEAD Binding:** Old base SHAs or conversational assertions are invalid merge authority. Merge readiness requires live verification of target `main` SHA and PR `head` SHA.
3. **Fail-Closed on Unaccessible Permissions:** If repository settings or branch protection endpoints are unaccessible (e.g. HTTP 403 or missing API scopes), C2 must report the permission boundary transparently and must never fabricate that protection is enabled.
4. **Bounded Frontier Enforcement:** C2 must reconcile PR sprawl before expanding work. Unstarted or duplicate PRs must be classified as `SUPERSEDED` or `HISTORICAL` rather than kept open indefinitely.
5. **Historical Capability Recovery Law:** Historical SAGE work is an asset until proven redundant. A closed PR or branch must never be classified as "done" or "integrated" without verifying its capability payload against current `main`. Missing capability deltas must be reconstructed rather than discarded.
