# SAGE FAILURE MEMORY

This file preserves verified historical SAGE execution mistakes as durable anti-regression knowledge.

---

## FAILURE 1: WRONG REPOSITORY/MAINLINE STATE
FAILURE: Running code or validation checks on stale branches or incorrect repository states.
ROOT CAUSE: Lack of git branch ancestry validation before running critical validation checks.
DETECTION: Checking branch merge base against `origin/main`.
PREVENTION RULE: Always verify ancestry and ensure local branch is correctly rebased on current `origin/main`.
PRE-COMMIT CHECK: Check `git log` and `git status` during pre-commit.
REGRESSION TEST OR ASSERTION: Assert `git merge-base --is-ancestor origin/main HEAD` returns 0.

---

## FAILURE 2: SCOPE DRIFT
FAILURE: Introducing unrelated features or modifying unrelated files within an active task.
ROOT CAUSE: Failure to bound modifications within the authorized task scope.
DETECTION: Discrepancy between modified file paths and authorized task metadata.
PREVENTION RULE: Restrict modifications strictly to target files declared in active task.
PRE-COMMIT CHECK: Check `git diff --name-only` against target files.
REGRESSION TEST OR ASSERTION: Assert set of modified files is a subset of authorized files.

---

## FAILURE 3: HISTORICAL EVIDENCE CONTAMINATION
FAILURE: Modifying previous/historical phase validation evidence files under `evidence_capture/`.
ROOT CAUSE: Lack of strict file-mutability gating for historical records.
DETECTION: Git status shows modifications to protected `evidence_capture/phase_*` files.
PREVENTION RULE: Ensure historical evidence remains 100% byte-for-byte immutable.
PRE-COMMIT CHECK: Check `git status` for modified protected evidence files and discard them if modified.
REGRESSION TEST OR ASSERTION: Assert no files matching `evidence_capture/phase_*` are modified.

---

## FAILURE 4: STOPPING BEFORE AUTHORIZED EXECUTION
FAILURE: Prematurely halting or failing to execute the actual target workload once authorization is given.
ROOT CAUSE: Confusing preflight/pre-requisite checks with execution itself.
DETECTION: Mission status stuck at `EXECUTION_AUTHORIZED` instead of reaching `EXECUTION_COMPLETE`.
PREVENTION RULE: Proceed to run and record the workload immediately upon receiving valid authorization.
PRE-COMMIT CHECK: Check that execution logs exist and contain run details.
REGRESSION TEST OR ASSERTION: Assert mission progression transitions to `EXECUTION_COMPLETE`.

---

## FAILURE 5: FALSE CAUSALITY
FAILURE: Attributing system state changes or capability status to arbitrary, unrelated actions.
ROOT CAUSE: Blind correlation without tracing causal inputs.
DETECTION: Capability marked `VALIDATED` without running its designated tests.
PREVENTION RULE: Always require verified, direct test-run evidence linked to the modified capability.
PRE-COMMIT CHECK: Check for test receipt linkages.
REGRESSION TEST OR ASSERTION: Assert capability revalidation requires successful test run.

---

## FAILURE 6: TEST/PASS OVERCLAIM
FAILURE: Reporting high test-pass counts or success metrics without executing the physical tests.
ROOT CAUSE: Relying on static or cached logs instead of dynamic test results.
DETECTION: Test count in report does not match actual pytest execution run output.
PREVENTION RULE: Extract test counts dynamically from real-time execution outputs.
PRE-COMMIT CHECK: Inspect actual test run outputs.
REGRESSION TEST OR ASSERTION: Assert test count matches the length of passed test lists.

---

## FAILURE 7: GOVERNANCE INVENTION
FAILURE: Creating new custom governance levels or rules on-the-fly without consensus.
ROOT CAUSE: Overriding established state machines with transient configurations.
DETECTION: State machine bypassed or customized without updating core schema.
PREVENTION RULE: Only follow the canonical 10-stage progression state machine.
PRE-COMMIT CHECK: Verify state transitions against `ExperimentalMissionState`.
REGRESSION TEST OR ASSERTION: Assert all transitions go through progression controller validation.

---

## FAILURE 8: AUTHORIZATION LEAKAGE
FAILURE: Allowing unprivileged or unauthorized commands to execute in protected namespaces.
ROOT CAUSE: Lack of permission gating on transition triggers.
DETECTION: Preflight checks bypassed.
PREVENTION RULE: Reject any execution where authorization is missing or low-confidence.
PRE-COMMIT CHECK: Check authority gate logs.
REGRESSION TEST OR ASSERTION: Assert transition is blocked if cognitive confidence is low.

---

## FAILURE 9: DUPLICATE INFRASTRUCTURE
FAILURE: Creating redundant state projectors, storage handlers, or workspace managers.
ROOT CAUSE: Failing to audit the codebase for existing reusable utilities.
DETECTION: Parallel classes with identical or overlapping features.
PREVENTION RULE: Audit existing codebase and reuse components (like `GoogleWorkspaceSyncManager`).
PRE-COMMIT CHECK: Perform grep and static review.
REGRESSION TEST OR ASSERTION: Assert no duplicate workspace managers are created.

---

## FAILURE 10: PROTECTED-BOUNDARY VIOLATION
FAILURE: Modifying files in frozen core namespaces (e.g., `sage/core/`, `sage/acr/`).
ROOT CAUSE: Attempting to patch structural files instead of working within designated areas.
DETECTION: Git status shows modification in protected namespaces.
PREVENTION RULE: Maintain complete immutability of core namespaces.
PRE-COMMIT CHECK: Assert no modified files in `sage/core/` or `sage/acr/`.
REGRESSION TEST OR ASSERTION: Assert no modified files in protected directories.

---

## FAILURE 11: RESEARCH-TO-CODE LEAKAGE
FAILURE: Promoting highly speculative research ideas directly into core code without validation.
ROOT CAUSE: Confusing speculative hypotheses with hard engineering requirements.
DETECTION: Experimental imports inside production files.
PREVENTION RULE: Enforce the One-Way Import Law (production files must never import experimental paths).
PRE-COMMIT CHECK: Static import analysis.
REGRESSION TEST OR ASSERTION: Assert no imports of `sage/experimental/` from production.

---

## FAILURE 12: PREMATURE ARCHITECTURE
FAILURE: Over-engineering solutions and building complex systems before a minimal slice is verified.
ROOT CAUSE: Anticipating hypothetical needs rather than building bounded features.
DETECTION: Unused classes and complex abstract interfaces.
PREVENTION RULE: Follow strict incremental development: Inspect → Bound → Implement.
PRE-COMMIT CHECK: Check for unused and overly complex structures.
REGRESSION TEST OR ASSERTION: Assert all code maps to verified, tested requirements.

---

## FAILURE 13: CHAT/ARCHIVE CONFUSION
FAILURE: Treating conversational chat summaries or instructions as official archive entries.
ROOT CAUSE: Failing to isolate human chat history from the immutable ledger.
DETECTION: Chat transcript logged as a system capability.
PREVENTION RULE: Only promote structured, verified evidence packages to the Master Archive.
PRE-COMMIT CHECK: Inspect the archive logs.
REGRESSION TEST OR ASSERTION: Assert Archive entries match standard JSON schemas.

---

## FAILURE 14: NEGATIVE-PATH COLLAPSE
FAILURE: Failing to test negative code paths, assuming positive outcomes.
ROOT CAUSE: Incomplete test coverage focusing only on success scenarios.
DETECTION: Tests do not assert failures or rollbacks when inputs are invalid.
PREVENTION RULE: Always write explicit tests for negative paths and fail-closed behaviors.
PRE-COMMIT CHECK: Review test cases for error/exception handling assertions.
REGRESSION TEST OR ASSERTION: Assert invalid inputs trigger appropriate exception/failure states.

---

## FAILURE 15: PREMATURE OPTIMIZATION
FAILURE: Optimizing code performance (e.g. caching, concurrent threads) before verifying correctness.
ROOT CAUSE: Misplaced engineering priorities over functional accuracy.
DETECTION: Complex thread-safety logic in unverified components.
PREVENTION RULE: Prioritize correctness first, optimize only after functional correctness is proven.
PRE-COMMIT CHECK: Check complexity metrics.
REGRESSION TEST OR ASSERTION: Assert simple, correct implementation precedes performance tuning.
