# SAGE Operator Acceptance State

Status: PROPOSED FOR GOVERNED IMPLEMENTATION
Defects: C2-OPS-001, C2-OPS-002

## Completion rule
A task, flight, PR, capability, or issue is CLOSED/ACCEPTED only when both gates are explicit PASS.

### Deterministic gate
- implementation is merged to canonical `main`
- CI passes for the exact merged SHA
- exact SHA is recorded in evidence

### Empirical gate
- operator/client end-to-end behavior is exercised through the actual execution interface(s)
- operator observation explicitly records PASS
- a non-repudiable repository evidence reference is attached

A deterministic PASS without empirical PASS is `ENGINEERING_VERIFIED`, never `ACCEPTED`.
An empirical PASS without deterministic PASS is `OPERATOR_OBSERVED`, never `ACCEPTED`.

## Required state
```yaml
operator_acceptance_state:
  mission_id: "<stable mission id>"
  canonical_git_sha: "<40-char sha>"
  main_goals: []
  side_goals: []
  active_flights: []
  deterministic_gate:
    ci_pass: false
    exact_sha_anchored: false
    merged_to_main: false
    status: FAIL
  empirical_gate:
    interfaces_tested: []
    operator_observation: PENDING
    evidence_ref: null
    status: FAIL
  acceptance_status: NOT_ACCEPTED
  open_defects: []
  evidence_refs: []
```

## Session bootstrap invariant
Before C2 issues an operational update, code modification, or execution directive in a new session, it MUST resolve canonical `main` and exact SHA; reconcile active PRs, CI, issues, and workflow state; rehydrate `main_goals`, `side_goals`, and `active_flights`; construct/refresh Operator Acceptance State; and fail closed if canonical state cannot be reconciled.

## Defect elevation
Operator-reported drift, missing context, execution gaps, or premature completion is a first-class operational defect even when unit/CI tests pass. Each defect MUST map to repository evidence and remain open until the affected empirical gate is re-tested and passes.
