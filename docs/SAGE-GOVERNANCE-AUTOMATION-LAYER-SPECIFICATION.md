# SAGE GOVERNANCE AUTOMATION LAYER (SAGE-GAL) PHASE 1 SPECIFICATION

## 1. Executive Summary & Purpose
The **SAGE Governance Automation Layer (SAGE-GAL)** is an experimental capability designed to reduce manual verification cycles while preserving SAGE's immutable governance laws. It functions strictly as a **verification assistant** and **not** an autonomous authority layer. SAGE-GAL automates preflight checks, protected boundary scans, duplicate work checks, test execution, and evidence package assembly. It does **not** automate merges, promotions, code modifications, or human approval bypasses.

---

## 2. Five Required Capabilities

### 2.1 Repository Preflight
SAGE-GAL automatically gathers the current repository branch state, changed file list, and diff scope.
* **Checks Enforced:** Scans the active workspace utilizing git commands (`git status`, `git diff`) or fallback OS path listings.
* **Standard Output Format:**
  ```
  Changed Files: [list of files]
  Approved Scope: [allowed folders, e.g. sage/experimental/, tests/experimental/]
  Unexpected Files: [list of files violating scope]
  Scope Status: [CLEAN | ACCIDENTAL_EXPANSION_DETECTED]
  ```

### 2.2 Protected Boundary Scanner
SAGE-GAL programmatically verifies that files under production core directories remain completely untouched.
* **Monitored Paths:**
  * `sage/runtime/`
  * `sage/core/`
  * `sage/acr/`
  * `sage/agents/`
* **Checks Enforced:** Ensures zero modifications or untracked additions inside these paths.
* **Standard Output Format:**
  ```
  Protected Paths: [list of monitored directories]
  Modified: YES/NO
  Violation: YES/NO
  ```

### 2.3 Existing Capability Detection
To prevent duplicate implementations and accidental milestone re-openings, SAGE-GAL crawls the repository codebase, search index, and specifications for existing keyword occurrences.
* **Searched Elements:** Matches against existing python classes, validators, active experiments, evidence packages, and INDEX entries.
* **Standard Output Format:**
  ```
  Existing Match: [list of files/classes matched]
  Related Checkpoint: [identified previous milestone]
  Duplicate Risk: [NONE | LOW | MEDIUM | HIGH]
  Recommendation: [PROCEED | STOP_DUPLICATE_WORKSTREAM]
  ```

### 2.4 Validation Runner
SAGE-GAL automates execution of the local testing suite, parsing outputs to calculate pass ratios and regression metrics.
* **Checks Enforced:** Programmatically runs targeted test files or full pytest suites, capturing stderr/stdout and return codes.
* **Standard Output Format:**
  ```
  Tests Passed: [count]
  Tests Failed: [count]
  Regression Status: [CLEAN | REGRESSIONS_DETECTED]
  ```

### 2.5 Evidence Generator
Consolidates all check results into a single structured, signed JSON file to simplify final human review.
* **Required Properties:**
  * `gal_run_id`: Unique identifier (e.g. `gal_[uuid/md5]`).
  * `commit_identifier`: Current repository SHA-1 commit hash.
  * `changed_files`: List of files modified in the active workspace.
  * `boundary_status`: Results of the Protected Boundary Scan.
  * `test_results`: Number of tests run, passed, and failed.
  * `evidence_references`: Path references to related artifacts.
  * `human_review_status`: Explicitly set to `"PENDING_HUMAN_SIGN_OFF"`.

---

## 3. Security Boundary Preservation
SAGE-GAL operates purely as a read-only, non-mutating auditing tool. It is restricted entirely to `sage/experimental/` and cannot write to or alter the active state of core runtime operations.
