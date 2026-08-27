# SAGE Local Integrity Kernel (LIK)

## Purpose

LIK is the local admissibility boundary between C2 mission intent and a state-changing promotion decision. C2 may authorize a mission, but a promotion is admissible only when the execution itself proves that it is the execution C2 authorized.

This is a **SLSA-aligned provenance control**, not a claim that SAGE itself is SLSA Build Level 3 compliant. SLSA Build Level 3 additionally requires a hardened build service with trusted, non-forgeable provenance and isolation between concurrent builds.

## Canonical execution identity

A live receipt is identified by the complete tuple:

`(wave_id, flight_id, executed_head, base_commit, workflow_run_id, job_id, artifact_digest)`

A receipt is valid only if:

1. every identity field is present and schema-valid;
2. `executed_head` equals the expected runtime commit exactly;
3. `base_commit` equals the authorized base exactly;
4. workflow run and job identities equal the expected execution context exactly;
5. the artifact digest is independently observed as `sha256:<64 hex>` and equals the receipt digest;
6. `passed == true`;
7. every required front reaches `RECEIPT_VALID`.

There is no baseline fallback, set-membership match, `latest` receipt, or `receipts[0]` selection.

## Evidence storage

Live evidence is addressed by identity:

`evidence_capture/waves/<wave_id>/<executed_head>/<flight_id>_receipt.json`

The registry is append-only. A second write to the same identity path is a hard error.

Legacy flat files such as `evidence_capture/multi_session_velocity_wave_evidence.json` are historical indexes/fixtures only. They are not authoritative gate inputs.

## Front state machine

`EXPECTED -> SCHEDULED -> STARTED -> EXECUTED -> RECEIPT_PRESENT -> RECEIPT_VALID -> RECONVERGED`

`MISSING`, `SKIPPED`, `UNOBSERVED`, `STALE`, or `CONTRADICTORY` evidence cannot transition to `RECEIPT_VALID` and therefore cannot reconverge.

GitHub Actions dependency skips are especially important: a downstream job that uses `needs` may itself be skipped when an upstream job fails or is skipped. A reconvergence gate must explicitly inspect the observed front set and fail closed rather than treating a skipped dependency as success.

## Architecture boundary

- **C2:** intent, authorization package, mission ordering.
- **Flight executors:** bounded work and generation of execution receipts.
- **LIK:** local deterministic validation of execution identity and artifact integrity.
- **Reconvergence:** requires all five independently valid front receipts.
- **Promotion/CAS gate:** only admissible after reconvergence; merge/ref movement must be serialized against fresh main HEAD.
- **Observability:** traces and indexes may summarize execution but cannot become the authority for promotion.

## Historical lessons

- PR #248 established the need for dynamic execution identity rather than configured/static identity.
- PR #275 exposed concurrent mutation of shared evidence files.
- PR #276 delivered the BuildJumpWaveEngine but also demonstrated that checked-in evidence can become stale as soon as the commit moves.
- The corrective architectural rule is therefore stronger than "bind evidence to HEAD": **bind live evidence to the full execution identity and keep it outside mutable shared flat-file gate paths.**

## External alignment

SLSA requires provenance to identify the output and how it was produced, and its Build L3 isolation requirements explicitly address concurrent builds influencing one another. GitHub Actions also documents that skipped/failed `needs` jobs propagate skips unless a downstream job deliberately uses `always()`. These properties are incorporated into LIK's fail-closed model.
