# SAGE Merge Convergence Policy

This document establishes the permanent merge convergence policy for all future SAGE autonomous operations and development work.

---

## 1. Context & Problem Statement
SAGE operates in a highly dynamic, multi-agent development environment. When long-running branches remain out-of-sync with the primary `main` branch, they frequently modify the same operational state documents (e.g., `docs/master/MASTER_SNAPSHOT.md`, `docs/master/SESSION_STATE.md`) that are updated on `main` as milestones complete.

This parallel modification has previously caused repeated documentation merge conflict loops and unnecessary synchronization cycles. To eliminate this class of conflict entirely while preserving the validated SAGE architecture, this **Merge Convergence Policy** defines a set of strict, deterministic, and automated guidelines for branching, synchronizing, and resolving conflicts.

---

## 2. Core Convergence Rules

### Rule 1: Authoritative Root
The latest `main` branch is the absolute, single source of truth and authoritative repository state. No branch, agent, or developer session may treat an unmerged branch as the baseline for operational state.

### Rule 2: Pre-Implementation Synchronization
Before any development, feature addition, or bug resolution begins:
1. Fetch the latest `main` branch.
2. Synchronize the local workspace with `main`.
3. Rebase the active branch onto `main` before starting any major implementation work.

### Rule 3: Operational State Document Ownership
Operational state documents, specifically:
- `docs/master/MASTER_SNAPSHOT.md`
- `docs/master/SESSION_STATE.md`

belong to the latest validated state of the `main` branch. These documents must always converge directly to the version on `main`.
- **No recursive historical merges** of these operational files are allowed.
- When merging, begin with the latest `main` version of these files as the base.
- Apply only the newly validated, current session's operational states to these documents.
- Discard obsolete or duplicate history.

### Rule 4: Documentation-Only Conflict Resolution
If a merge conflict occurs and is restricted *solely* to these operational documents:
1. Preserve the latest validated `main` version of the files.
2. Manually integrate only the newly validated operational information (e.g., the new sprint task or milestone summary).
3. Rerun verification tests to confirm runtime integrity.
4. Finalize the synchronization immediately, preventing any recursive documentation merge loops.

### Rule 5: Baseline Re-Branching (Circuit Breaker)
If repeated synchronization attempts fail or become bloated with complex historical merge conflicts:
- **Do not continue merging recursively.**
- Create a brand new, clean branch directly from the latest `main`.
- Replay (cherry-pick or manually port) only the validated implementation commits.
- Completely discard the obsolete or messy merge history.
- Continue working from the clean baseline.

The ultimate goal of SAGE operations is **state convergence**, not the preservation of intermediate development merge artifacts.

---

## 3. Automatic Completion Procedure (Milestone Protocol)
To ensure absolute reliability, every future milestone must execute the following automated steps before completion:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MILESTONE COMPLETION LIST                       │
├────────────────────────────────────────────────────────────────────────┤
│  1. Synchronize with latest main (pull & rebase)                       │
│  2. Verify Runtime (SageRuntime instantiation & state rehydration)    │
│  3. Verify API (REST endpoint mapping & health)                        │
│  4. Verify CLI (CLI sub-commands and output validity)                  │
│  5. Run pytest (Full python test suite validation)                     │
│  6. Run Ruff (Code style and quality rules validation)                 │
│  7. Run Black (Consistent format checking)                             │
│  8. Verify Documentation Integrity (INDEX.md & file mapping checks)    │
│  9. Verify Archive Integrity (Master Archive record verification)      │
│ 10. Update MASTER_SNAPSHOT once                                        │
│ 11. Update SESSION_STATE once                                          │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
            ┌──────────────────────────────────────────────┐
            │ Automatic Merge (if permissions allow)       │
            │                      OR                      │
            │ Exactly One Clean Merge-Ready Pull Request   │
            └──────────────────────────────────────────────┘
```

---

## 4. Repository Rules & Architecture Constraints
All SAGE agents and engineers must obey these constraints to prevent architectural drift:
- **Do not redesign validated architecture**: The SAGE Autonomous Continuity Runtime (SAGE-ACR) is a proven, validated platform.
- **Do not duplicate persistence**: Use the authoritative `sage_state.json` or `.sage/` directory; do not write parallel custom state serializers.
- **Do not duplicate routing**: Always route external events and context ingestion through the single authoritative Continuity Bridge (`ingest_session_payload` inside `SageRuntime`).
- **Do not rebuild completed systems**: Always extend the existing SAGE Runtime and components in `sage/service.py`, `sage/integration.py`, and other core modules rather than writing redundant modules.
- **Maintain canonical memory**: Keep the repository as the single source of truth for engineering memory and platform continuity.
