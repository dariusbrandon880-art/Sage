# SAGE Five-Flight Campaign v1

Status: EXECUTION CANDIDATE
Base: `bb5612c84290d89bec6a67426eab70fbbdfa9fbb`

## Mission

Execute the current longitudinal capability frontier as one connected campaign while preserving independent evidence gates. The campaign tests whether governed experience compounds across horizon, recovery, reuse, retention, and regression.

## Flight 003 — Horizon Residual

**Question:** Does reliability degrade as the execution horizon expands, and does SAGE change that degradation relative to a matched baseline?

**Required evidence:** matched short/long baseline and SAGE observations, authentic provenance, horizon identifiers, success/failure, elapsed/cost telemetry where available.

**Verdict boundary:** residual is descriptive evidence only; it cannot itself qualify capability.

## Flight 004 — Recovery

**Question:** When a controlled failure occurs, does SAGE recover more reliably and at lower recovery cost than the matched baseline?

**Required evidence:** pre-failure state, injected failure identity, post-failure state, recovery attempt count, recovery outcome, recovery cost/latency, provenance.

**Invariant:** the failure must be observable and attributable; recovery cannot be inferred from final success alone.

## Flight 005 — Reuse

**Question:** Does a later episode measurably benefit from a prior successful experience without importing unverified state?

**Required evidence:** first-episode receipt/reference, reuse decision/reference, matched repeat task, outcome delta, provenance chain.

**Invariant:** memory/reuse is a hypothesis until the later outcome demonstrates benefit.

## Flight 006 — Retention / Regression

**Question:** Does demonstrated improvement survive a fresh session while unrelated capability remains stable?

**Required evidence:** cross-session identity continuity, retained-task result, regression probes, comparison to baseline, durable evidence lineage.

**Invariant:** retention and regression are separate measurements; passing retention does not erase a regression.

## Flight 007 — Compound

**Question:** Does SAGE compound the preceding advantages across a harder connected trajectory?

**Composition:** horizon + controlled failure/recovery + reuse + cross-session retention + regression resistance + provenance/authorization/continuity.

**Required evidence:** all component observations linked to one locked evaluation plan and independently replayable receipts.

**Verdict boundary:** only the existing LongitudinalCapabilityEvaluator may produce PASS/HOLD/NEGATIVE_RESULT. No campaign artifact may promote itself.

## Baseline Symmetry

Every flight uses the same mission/task definitions, identifiers, environmental assumptions, and measurement semantics for baseline and SAGE. Differences in execution are evidence only when attributable to the governed intervention.

## Fail-Closed Rules

- Missing telemetry => HOLD.
- Ambiguous attribution => HOLD.
- Cross-session identity mismatch => HOLD/NEGATIVE_RESULT according to evaluator semantics.
- Unauthorized mutation => NEGATIVE_RESULT.
- Fabricated or synthesized observation => invalid flight evidence.
- CI success => machine gate only, never capability proof.
- Failure is retained as durable negative knowledge.

## Campaign Loop

LOCK → BASELINE → SAGE → OBSERVE → RECOVER → REUSE → RETAIN → ATTACK REGRESSION → COMPOUND → INDEPENDENT C2 VERIFY → PASS / HOLD / NEGATIVE_RESULT → COMPOUND NEXT FRONTIER

## Production-Speed Boundary

The five flights are one campaign, but evidence remains independently inspectable. Build connected fixtures, plans, and telemetry plumbing together where their contracts are stable. Do not serialize independent work unnecessarily. Do not skip a verification gate merely to preserve speed.

## STOP

Stop the campaign only at a genuine technical/evidentiary blocker, an authorization boundary, or after Flight 007 produces a classification requiring independent verification. Do not invent missing observations or convert descriptive metrics into capability claims.
