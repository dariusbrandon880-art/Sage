# SAGE Assembly-Line Preflight / Durable Failure Memory

This document maps SAGE's verified historical execution failures into a durable, executable development gate, fully complying with SAGE core governance directives.

## 1. Durable Failure-Memory Profiles

| Failure ID | Core Cause / Lesson | Executable Detection | Fail-Closed Result |
| :--- | :--- | :--- | :--- |
| **STATE-DRIFT** | Current branch is not derived from latest mainline HEAD. | `git merge-base --is-ancestor origin/main HEAD` check. | Reject submission at Preflight gate with stale state error. |
| **EVIDENCE-MUT** | Modification of historically validated Phase 4 evidence files. | Scans `evidence_capture/phase_4_*` for modification. | Reject submission at Preflight gate with evidence contamination error. |
| **IMPORT-LAW** | Core production files statically import from experimental paths. | AST parsing of core files for `sage.experimental` imports. | Reject submission at Preflight gate with One-Way Import Law violation. |
| **CORE-MUT** | Mutation of core production files without explicit authorization. | Scans `sage/core/`, `sage/acr/`, etc. for modifications. | Reject submission with protected-core boundary violation. |

## 2. Executable Development Gate

The preflight script is located at `scripts/jules_preflight.py` and is run automatically before commits or submissions are authorized.
