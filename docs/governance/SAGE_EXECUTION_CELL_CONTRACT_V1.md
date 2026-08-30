# SAGE Execution Cell Interface Contract v1.0.0

**Status:** Governance contract / execution substrate boundary  
**Scope:** Infrastructure underneath the existing Big Jump Wave and Multi-Session Velocity architecture.

## Purpose

The Execution Cell is the bounded actuator between C2 mission control and an authorized execution substrate. It makes repository execution mechanically verifiable without attempting to expand ChatGPT's client permissions.

The contract is substrate-agnostic. GitHub Actions, a local MCP/daemon bridge, or another authorized runner may implement it, but every substrate must return the same class of evidence and obey the same fail-closed invariants.

## Canonical flow

```text
C2 / ChatGPT
    -> signed mission package
    -> Execution Cell validation
    -> isolated execution
    -> tests + evidence
    -> attestation
    -> remote Git verification
    -> C2 reconvergence
```

## Invariants

### 1. Signed mission package

Every consequential execution request carries a typed mission package containing `mission_id`, `target_repo`, the exact canonical 40-character `canonical_head_sha`, explicit allowed paths, explicit allowed commands, five-flight allocation, collision state, and a session/cryptographic signature.

A short, padded, guessed, or otherwise non-canonical SHA is invalid.

### 2. Exact command allowlist

The execution substrate may execute only exact commands present in `allowed_commands`. Shell composition tokens such as `&&`, `;`, pipes, command substitution, backticks, and embedded newlines are rejected by the contract validator.

This contract does not authorize unrestricted shell access.

### 3. Path allowlist

A mission package declares the repository paths it may touch. Absolute paths and traversal components are rejected. The executor must fail closed when an operation falls outside the declared boundary.

### 4. SHA pinning

The executor must establish that the actual checkout HEAD equals `canonical_head_sha` before execution. If the target changes unexpectedly, execution is aborted unless C2 explicitly issues a new mission package for the new canonical SHA.

### 5. Evidence derives from execution

The executor, not the LLM narrative layer, generates execution receipts. `executed_head_sha` must come from the actual repository checkout. Evidence must identify the resulting commit relationship rather than cosmetically rewriting a stale SHA.

### 6. Fail-closed reconvergence

A run is not acceptance-eligible if tests fail, the attestation is incomplete, the exact HEAD cannot be verified, a collision is detected, or the shadow/wagering boundary is violated.

The resulting commit may legitimately differ from the execution base SHA. What matters is that the parent/base relationship and produced SHA are independently verifiable.

### 7. Existing architecture is canonical

The Execution Cell does **not** redesign Big Jump, Multi-Session Velocity, the Five-Flight system, Sports learning, or C2 reconvergence. It supplies a governed actuator underneath those existing mechanisms.

For repair/check missions, the existing five flight slots may be temporarily re-aligned to repo truth, intelligence, repair, verification/evidence, and reconvergence. They remain dynamic slots rather than permanent domains.

## Required attestation

A conforming substrate returns:

- `mission_id`;
- substrate identity;
- `PASS`/`FAIL` status;
- exact process exit code;
- exact `executed_head_sha`;
- exact `produced_head_sha` when a commit is produced;
- evidence receipt path;
- exact-head verification result;
- test pass rate;
- collision result;
- shadow/wagering boundary result;
- optionally a digest of captured stderr for failed execution.

An attestation is evidence of execution state, not permission to declare success. C2 independently verifies the remote Git state and acceptance boundary.

## Substrate implementations

### GitHub Actions

Use an ephemeral GitHub-hosted runner with a narrowly scoped workflow trigger. The workflow should check out the declared SHA, validate the mission package, execute only the allowlisted entry point(s), persist evidence, and publish through an explicitly authorized branch/PR workflow.

### Local MCP / daemon

Use an explicitly authorized local process with an isolated checkout. The process validates the same mission package and produces the same attestation contract. Local execution does not bypass SAGE governance or remote verification.

## Security boundary

The Execution Cell must never acquire credentials autonomously, weaken repository protection, silently broaden command/path scope, fabricate test results, synthesize sports outcomes, or convert an unavailable runtime into a claimed successful execution.

When the required execution substrate is unavailable, return an explicit `EXECUTION_UNAVAILABLE` result to C2. Do not manufacture a receipt.

## Acceptance boundary

```text
mission package valid
    + exact checkout SHA verified
    + allowed scope verified
    + collision clear
    + execution exit code 0
    + required tests pass
    + evidence generated by executor
    + evidence exact-head verified
    + produced commit relationship verified
    + remote push verified
    + remote CI/state verified
    = C2 may accept / merge
```

Any failed condition leaves the mission in a non-accepted state.

## Relationship to SAGE governance

This contract is an implementation substrate for the existing C2 whole-mission repair directive and direct-repair accountability lesson. It exists so that C2 can remain accountable for closure while Jules or another authorized executor can provide scalable real runtime execution.

**Operating maxim:**

> C2 commands. The Execution Cell acts within bounds. Git records reality. Evidence proves execution. C2 reconverges and closes.
