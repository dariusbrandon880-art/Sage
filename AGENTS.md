# SAGE AGENTS & ANTI-REGRESSION EXECUTIVE PROTOCOL (AGENTS.md)

## INTRODUCTION & GENERAL MANDATE

This document serves as the authoritative, durable, and non-bypassable anti-regression instruction set for Jules and all other AI agents executing tasks in the SAGE (Autonomous Continuity Runtime) repository. It translates historical engineering, communication, and governance failures into concrete, verifiable, and executable prevention rules.

Every agent MUST read this file in full before planning or executing any modifications to the repository.

---

## Part 1: The 15 Core Failure Classes (Jules Runtime Errors)

### FAILURE CLASS 01 — WRONG REPOSITORY STATE
- **FAILURE:** WRONG REPOSITORY STATE
- **ROOT CAUSE:** Blind trust in PR descriptions/context notes, overlooking Git history, and assuming a branch is fully synchronized with `origin/main` without validating the actual current repository tree truth first.
- **DETECTION:** Running `git status`, `git branch -a`, or `git log --oneline -n 10` to query local ancestry, checking for diverged commits, and verifying workspace cleanliness.
- **PREVENTION RULE:** Prioritize local checkout truth. Always query git to verify that HEAD has the correct ancestral lineage of main and that the working tree is clean before modifying files. Never reconstruct a supposedly merged capability from an unmerged branch.
- **PRE-COMMIT CHECK:** Execute branch lineage validation and inspect the git tree in preflight checkers.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** `scripts/jules_preflight.py` verifies branch ancestry and dirty states before authorizing changes.

### FAILURE CLASS 02 — SCOPE DRIFT
- **FAILURE:** SCOPE DRIFT
- **ROOT CAUSE:** Over-helpfulness, lack of boundary awareness, or over-engineering leading to uncontrolled modifications outside the specified boundary.
- **DETECTION:** Running `git diff --name-only` and verifying that changed files lie strictly within the authorized scope of work.
- **PREVENTION RULE:** Treat task boundaries as hard, absolute constraints. If a task is CI-only: application code, tests, docs, evidence, and runtime file changes MUST equal ZERO.
- **PRE-COMMIT CHECK:** Check the diff's modified file list against the declared scope rules in pre-commit scripts.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Ensure non-conforming file lists trigger exit codes in the preflight checker.

### FAILURE CLASS 03 — HISTORICAL EVIDENCE CONTAMINATION
- **FAILURE:** HISTORICAL EVIDENCE CONTAMINATION
- **ROOT CAUSE:** Uncontrolled test/verification suites writing to historical logs, or resetting file trees indiscriminately.
- **DETECTION:** `git status` showing modified files under `evidence_capture/phase_4_*` or `evidence_capture/phase_5_*`.
- **PREVENTION RULE:** Historical Phase 4 and Phase 5 evidence capture records are completely IMMUTABLE. Never regenerate or alter them merely because a new task executed. If historical records change unexpectedly, STOP execution instantly.
- **PRE-COMMIT CHECK:** Verify that git diff lists 0 modifications to `evidence_capture/phase_4_*` and `evidence_capture/phase_5_*`.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Assertion checking for any altered historical files using cryptographic hash comparisons.

### FAILURE CLASS 04 — STOPPING BEFORE AUTHORIZED EXECUTION
- **FAILURE:** STOPPING BEFORE AUTHORIZED EXECUTION
- **ROOT CAUSE:** Equating "ready to proceed", planning, static inspection, or mock successes with complete workload execution.
- **DETECTION:** Verifying that permanent state updates (like `operational_capability_registry.json` or live Master Archive files) have been updated with real transaction logs rather than mock indicators.
- **PREVENTION RULE:** Do not stop at a planning, inspection, or mock state. Execute the authorized workload until the target boundary is reached, an explicit blocker is hit, or human interaction is required.
- **PRE-COMMIT CHECK:** Verify that actual execution logs are generated in `evidence_capture/` post-execution.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Check that real run receipts or state mutations are present on disk.

### FAILURE CLASS 05 — FALSE CAUSALITY
- **FAILURE:** FALSE CAUSALITY
- **ROOT CAUSE:** Superficial semantic correlation (such as imports, shared objects, logging, serialization, sequential unrelated calls, or tests alone) rather than behavioral intervention testing.
- **DETECTION:** Running behavioral intervention tests (e.g. disabling or mutating component A, then measuring if component B's observable behavior is materially changed).
- **PREVENTION RULE:** Claiming causal composition (A → B) requires demonstrating that A materially and observably changes B's runtime behavior.
- **PRE-COMMIT CHECK:** Inspect integration tests for real state/assertion coupling rather than empty import checks.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Assert that changing state values in A propagates to observable results in B.

### FAILURE CLASS 06 — TEST/PASS OVERCLAIM
- **FAILURE:** TEST/PASS OVERCLAIM
- **ROOT CAUSE:** Equating isolated mock-heavy unit test success with physical runtime execution, downstream state persistence, evidence generation, or operator observation.
- **DETECTION:** Checking if tests only use in-memory mocks without ever calling disk operations or checking live files.
- **PREVENTION RULE:** Green tests establish *test success*, not system reality. Inspect the actual persistent filesystem, registries, and logs to verify real-world behavioral outcomes.
- **PRE-COMMIT CHECK:** Verify that test coverage includes state assertion on persistent files.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Check that files like `operational_capability_registry.json` are modified with valid values during the run.

### FAILURE CLASS 07 — GOVERNANCE INVENTION
- **FAILURE:** GOVERNANCE INVENTION
- **ROOT CAUSE:** Unwillingness to halt execution when facing a strict boundary, prompting the invention of mock authority, alternative approval state machines, or bypass tokens.
- **DETECTION:** Code containing custom auth logic, bypassed permission decorators, or simulated human signatures.
- **PREVENTION RULE:** If an existing authorization mechanism cannot support the next action, REPORT: GOVERNANCE GAP. Do not invent bypass mechanisms, authorization tokens, or replacement state machines.
- **PRE-COMMIT CHECK:** Scan for new unauthorized decorators, auth structures, or bypassed checks in `sage/core/spek.py`.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Preflight checkers raise errors on unauthorized authorization files or tokens.

### FAILURE CLASS 08 — AUTHORIZATION LEAKAGE
- **FAILURE:** AUTHORIZATION LEAKAGE
- **ROOT CAUSE:** Creeping scope assumptions; assuming "implied permission" based on adjacent successes (SUCCESSFUL RESULT → AUTHORIZATION FOR UNRELATED WORK).
- **DETECTION:** Analyzing if the current branch includes files modified outside of the specific task-related boundary.
- **PREVENTION RULE:** Every consequential continuation must pass its own specific preflight, safety, and authorization boundaries. Never infer broad authorization from single successful results.
- **PRE-COMMIT CHECK:** Check that active scopes explicitly map to the task ID.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Assertion that task inputs align exactly with modified scopes.

### FAILURE CLASS 09 — DUPLICATE INFRASTRUCTURE
- **FAILURE:** DUPLICATE INFRASTRUCTURE
- **ROOT CAUSE:** Inadequate code exploration and failure to locate pre-existing libraries or components.
- **DETECTION:** Search for redundant class definitions or overlapping logic (e.g. duplicating `MissionProgressionController` or `SAGEChangeImpactAnalyzer`).
- **PREVENTION RULE:** Search for existing consumers, registries, preflight checks, and transition controls before creating any new capability. Prefer minimum connection.
- **PRE-COMMIT CHECK:** Scan for duplicated models or functions during structural audit checks.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Verify reuse of core libraries like `sage/archive/core.py`.

### FAILURE CLASS 10 — PROTECTED-BOUNDARY VIOLATION
- **FAILURE:** PROTECTED-BOUNDARY VIOLATION
- **ROOT CAUSE:** Bypassing strict modular separation to quickly hack in an experimental capability.
- **DETECTION:** `git status` showing modified files under core namespaces.
- **PREVENTION RULE:** Never modify frozen core namespaces (`sage/runtime/`, `sage/core/`, `sage/acr/`, `sage/agents/`) unless explicitly and directly authorized. Keep experiments strictly in `sage/experimental/`.
- **PRE-COMMIT CHECK:** Scan modified file paths to block edits under core folders unless authorized.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Preflight script check fails if any file under protected folders is modified without explicitly overriding flags.

### FAILURE CLASS 11 — RESEARCH → CODE LEAK
- **FAILURE:** RESEARCH → CODE LEAK
- **ROOT CAUSE:** Importing experimental or speculative modules statically in production namespaces.
- **DETECTION:** Scan core files for imports referencing `sage/experimental/`.
- **PREVENTION RULE:** Maintain the One-Way Import Law: core namespaces must NEVER statically import from experimental paths. Speculative designs must remain non-executing.
- **PRE-COMMIT CHECK:** Parse AST of all python files in core namespaces to check for imports of `sage.experimental`.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** AST-based verification test asserting `not_imports_experimental`.

### FAILURE CLASS 12 — PREMATURE ARCHITECTURE
- **FAILURE:** PREMATURE ARCHITECTURE
- **ROOT CAUSE:** Over-engineering based on imagined future needs.
- **DETECTION:** Uncalled methods, unused classes, or speculative structures lacking callers in existing code.
- **PREVENTION RULE:** Prove the minimum active consumer, existing capability, and missing connection before writing any architectural infrastructure.
- **PRE-COMMIT CHECK:** Verify all new classes have real calling paths from existing code or active tests.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Dead code check.

### FAILURE CLASS 13 — CHAT/ARCHIVE CONFUSION
- **FAILURE:** CHAT/ARCHIVE CONFUSION
- **ROOT CAUSE:** Trusting conversational memory/assumptions over physical repository truth.
- **DETECTION:** Discrepancy between code comments/variable defaults and Master Archive schemas.
- **PREVENTION RULE:** Durable repository/archive state is authoritative. Do not reconstruct project truth from chat logs when physical evidence is present.
- **PRE-COMMIT CHECK:** Verify baseline schemas match archive entries exactly.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Automated comparison against `Main Archive/INDEX.md`.

### FAILURE CLASS 14 — NEGATIVE-PATH COLLAPSE
- **FAILURE:** NEGATIVE-PATH COLLAPSE
- **ROOT CAUSE:** Reducing complex state representation to make assertions pass easily.
- **DETECTION:** Checking if tests check for a generic "failure" without verifying the specific transition result.
- **PREVENTION RULE:** Preserve distinct meanings of negative outcomes (`ACCEPT`, `REJECT`, `FAIL-CLOSED`, `ROLLBACK`, `RECOVERY`, `VALIDATION_REQUIRED`). Ensure error-trapping distinctness is fully represented in tests.
- **PRE-COMMIT CHECK:** Inspect assertions to ensure they check the correct state transitions.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Tests verifying distinct transition logic paths in state controllers.

### FAILURE CLASS 15 — PREMATURE OPTIMIZATION
- **FAILURE:** PREMATURE OPTIMIZATION
- **ROOT CAUSE:** Optimizing based on guesswork instead of profiling data.
- **DETECTION:** Optimization PRs/changes without profiling data or trace metrics.
- **PREVENTION RULE:** Do not optimize latency, complexity, or tokens before identifying the causal bottleneck with empirical metrics.
- **PRE-COMMIT CHECK:** Insist on benchmark data for optimization submissions.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Performance metrics tracking under `evidence_capture/`.

---

## Part 2: SAGE Core History Failures (Failure A to J)

### FAILURE A — DOCUMENTATION-FIRST BEHAVIOR
- **FAILURE:** DOCUMENTATION-FIRST BEHAVIOR
- **ROOT CAUSE:** Treating structural descriptions, diagrams, summaries, or log messages as actual executing proof of a capability.
- **DETECTION:** Files present in docs but completely absent from actual implementation or test files.
- **PREVENTION RULE:** Always verify running implementation with tests and active, cryptographically signed files under `evidence_capture/`.
- **PRE-COMMIT CHECK:** Verify existence of implementation for all documented capability classes.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Registry match checks in `tests/test_capability_registry.py`.

### FAILURE B — SIMULATION OVERCONFIDENCE
- **FAILURE:** SIMULATION OVERCONFIDENCE
- **ROOT CAUSE:** Overlooking environment-specific dependencies, assuming local test environment green statuses equate to physical production reality.
- **DETECTION:** Test suites lacking remote validation or environment-specific checks.
- **PREVENTION RULE:** Treat local green and production green as separate tracks. Validate deployment configuration parameters separately.
- **PRE-COMMIT CHECK:** Run production check scripts alongside local tests.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** `scripts/production_check.py` returns true in sandbox environment.

### FAILURE C — STATIC DEPENDENCY/EXPOSURE MODELING
- **FAILURE:** STATIC DEPENDENCY/EXPOSURE MODELING
- **ROOT CAUSE:** Trusting frozen configurations instead of dynamic live discovery.
- **DETECTION:** Discrepancies between static configuration files and actual module imports.
- **PREVENTION RULE:** Always use active, real-time discovery (like `SAGEChangeImpactAnalyzer`) to map changes.
- **PRE-COMMIT CHECK:** Automatically run the Change Impact Analyzer on changed files.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Verify `SAGEChangeImpactAnalyzer` returns correct dynamic dependencies.

### FAILURE D — UNKNOWN-STATE FREEZING
- **FAILURE:** UNKNOWN-STATE FREEZING
- **ROOT CAUSE:** Monolithic safety-check coupling.
- **DETECTION:** Observing a single failed component cause a complete global crash of unaffected systems.
- **PREVENTION RULE:** Use resilient, isolated safety gates (like `PrefrontalCortexSimulator`) to halt affected areas while preserving core system execution.
- **PRE-COMMIT CHECK:** Verify error-trapping and boundary limits in tests.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Tests verifying error-isolation under `tests/experimental/test_continuity_control.py`.

### FAILURE E — DISCRETE EPISTEMIC LABELS
- **FAILURE:** DISCRETE EPISTEMIC LABELS
- **ROOT CAUSE:** Aggressive semantic compression that discards vital decision context.
- **DETECTION:** Checking if transition parameters throw away detailed logs/data.
- **PREVENTION RULE:** Maintain structured multi-hypothesis representations (Epistemic Radar) when collapsing states would destroy critical details.
- **PRE-COMMIT CHECK:** Ensure data structures preserve error and warning metadata.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Assertion checking metadata is not lost in state transitions.

### FAILURE F — PROVENANCE OVERCONFIDENCE
- **FAILURE:** PROVENANCE OVERCONFIDENCE
- **ROOT CAUSE:** Confusing origin tracing with factual verification, assuming multiple outputs are independent when they share an upstream source.
- **DETECTION:** Tests that trust data without performing content validation or checking for correlated sources.
- **PREVENTION RULE:** Validate content integrity separately from provenance origin. Identify and model potential agent consensus bias.
- **PRE-COMMIT CHECK:** Verify that validation engines perform strict checksum audits.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Ensure validator fails if SHA-256 hashes differ.

### FAILURE G — CONTINUITY WITHOUT CAUSAL VALIDITY
- **FAILURE:** CONTINUITY WITHOUT CAUSAL VALIDITY
- **ROOT CAUSE:** Blind state serialization without validating chronological prerequisites.
- **DETECTION:** Rehydrating files directly without checking the signature or sequence of the receipt chain.
- **PREVENTION RULE:** Always validate preceding cryptographic receipts and sequential prerequisites before rehydrating session states.
- **PRE-COMMIT CHECK:** Verify that state rehydration tests include validation of chain integrity.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Check receipt chaining inside `tests/experimental/test_mission_control_bridge.py`.

### FAILURE H — MULTI-AGENT AGREEMENT BIAS
- **FAILURE:** MULTI-AGENT AGREEMENT BIAS
- **ROOT CAUSE:** Swarm echo-chamber effect.
- **DETECTION:** Multi-agent consensus without measuring source correlation or model variance.
- **PREVENTION RULE:** Model and track agent correlation. Treat shared-prompt consensus as a single observation rather than independent verification.
- **PRE-COMMIT CHECK:** Audit agent templates for diversity and independence.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Consensus discount metrics implemented in coordination modules.

### FAILURE I — DEPLOYMENT/ENVIRONMENT DIVERGENCE
- **FAILURE:** DEPLOYMENT/ENVIRONMENT DIVERGENCE
- **ROOT CAUSE:** Ignoring container virtualization limits or platform environmental variables.
- **DETECTION:** Deployment failures on platforms like Render despite green local pytest results.
- **PREVENTION RULE:** Run the dedicated `production_check.py` and verify all production dependencies (like FastAPI/Pydantic) are correctly locked.
- **PRE-COMMIT CHECK:** Automatically execute production readiness scripts as part of preflight checks.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Ensure poetry lock matches pyproject.toml exactly.

### FAILURE J — PREMATURE ARCHITECTURE LOCK-IN
- **FAILURE:** PREMATURE ARCHITECTURE LOCK-IN
- **ROOT CAUSE:** Over-investment in elegant abstractions before empirical falsification.
- **DETECTION:** Clean, abstract classes that contain zero operational implementation or are bypassed in real workloads.
- **PREVENTION RULE:** Keep future tech inside isolated experimental lanes. Do not define production interfaces for unvalidated research concepts.
- **PRE-COMMIT CHECK:** Check for unused interfaces in production directories.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Static checker for zero callers on interface classes.

---

## Part 3: ChatGPT Incident Workflow Failures (Failure K to O)

### FAILURE K — CONTINUITY FAILURE
- **FAILURE:** CONTINUITY FAILURE
- **ROOT CAUSE:** Context window slicing or lazy retrieval, failing to review full context leading to memory erasure.
- **DETECTION:** Proposing plans that contradict locked architectural baselines or duplicate existing features.
- **PREVENTION RULE:** Before answering, load and review `docs/master/MASTER_SNAPSHOT.md`, `docs/master/SESSION_STATE.md`, and `docs/labs/JULES_ONBOARDING_CONTINUITY_REPORT.md`.
- **PRE-COMMIT CHECK:** Validate that proposed actions align precisely with the current sprint targets in `SESSION_STATE.md`.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Check session state is loaded on boot.

### FAILURE L — STATE HANDLING FAILURE
- **FAILURE:** STATE HANDLING FAILURE
- **ROOT CAUSE:** Indiscriminate re-evaluation of locked baselines, treating validated milestones as planning invites.
- **DETECTION:** Planning changes to files/states that are marked as `VALIDATED` or `CLOSED` in the registry.
- **PREVENTION RULE:** Treat completed and verified milestones as immutable baselines. Focus strictly on the next logical execution step.
- **PRE-COMMIT CHECK:** Halt if any attempt is made to refactor locked/merged namespaces.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Version check in capability registry.

### FAILURE M — EXECUTION VELOCITY FAILURE
- **FAILURE:** EXECUTION VELOCITY FAILURE
- **ROOT CAUSE:** Post-hoc narrative justification and administrative bloat.
- **DETECTION:** Long chat messages containing no code, no tool calls, or no actual test runs.
- **PREVENTION RULE:** Prioritize execution over explanation. Execute the minimum code changes, verify them with tests, and present raw execution artifacts.
- **PRE-COMMIT CHECK:** Ensure code changes are verified immediately after applying.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Measure duration of execution loops to minimize narrative overhead.

### FAILURE N — PRIORITY DRIFT
- **FAILURE:** PRIORITY DRIFT
- **ROOT CAUSE:** Communication-heavy rather than code-heavy task orientation.
- **DETECTION:** Overly descriptive reports with zero modifications to the workspace.
- **PREVENTION RULE:** SAGE requires direct engineering support. Direct implementation, concrete code integration, and test execution are our primary value.
- **PRE-COMMIT CHECK:** Verify code or script files are actually written and saved.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** File change verification on every task turn.

### FAILURE O — CONTINUITY PRESERVATION FAILURE
- **FAILURE:** CONTINUITY PRESERVATION FAILURE
- **ROOT CAUSE:** Collapsing chronological progression into a single unorganized heap.
- **DETECTION:** Attempting to execute milestone 3 tasks before milestone 1 is verified on disk.
- **PREVENTION RULE:** Always verify that previous steps are locked and fully registered in `INDEX.md` or `operational_capability_registry.json` before initiating adjacent tasks.
- **PRE-COMMIT CHECK:** Read and verify prerequisite steps before initializing a new task state.
- **REGRESSION TEST OR ASSERTION, IF JUSTIFIED:** Step-by-step state controller transition assertions.

---

## Part 4: Mandatory Assembly-Line Preflight Checklist

Every development task MUST run through this precise assembly-line preflight sequence:

```
           [ JULES TASK INTAKE ]
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 1. FAILURE MEMORY Check             │ - Read AGENTS.md and verify no violations.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 2. REPOSITORY TRUTH Check           │ - Verify git HEAD ancestry and branch.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 3. SCOPE Check                      │ - Ensure 0 changes outside scope.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 4. PROTECTED-BOUNDARY Check         │ - Ensure core namespaces are untampered.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 5. AUTHORIZATION Check              │ - Validate explicit authorization keys.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 6. EXISTING-CONSUMER Search         │ - Search codebase before writing anything.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 7. EXECUTE changes                  │ - Apply targeted code updates.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 8. CAUSALITY Check                  │ - Validate changes materially alter tests.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 9. NEGATIVE-PATH Check              │ - Verify failures trigger distinct outcomes.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 10. EVIDENCE Check                  │ - Ensure immutable evidence is untampered.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 11. WORKTREE / DIFF Check           │ - Verify no untracked file pollution.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 12. TARGETED TESTS                  │ - Run tests specific to modified files.
  └──────────────────┬──────────────────┘
                     │
                     ▼
  ┌─────────────────────────────────────┐
  │ 13. FULL TESTS                      │ - Run pytest to confirm zero regressions.
  └──────────────────┬──────────────────┘
                     │
                     ▼
                 [ REAL ]
```

This checklist is programmatically enforced via `scripts/jules_preflight.py`.
