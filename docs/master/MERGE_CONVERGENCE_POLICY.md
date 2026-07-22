# SAGE SEMANTIC MERGE CONVERGENCE POLICY

This document defines SAGE's permanent, immutable Merge Convergence Policy to resolve developer/agent merge conflicts cleanly, avoid git commit loops, and maintain state synchronization across connected workspaces.

---

## 1. General Git Principles
* **Authoritative Source**: The `main` branch of SAGE's repository is the single authoritative source of truth.
* **Pre-Requisite Synchronisation**: SAGE must pull, rebase, and synchronize against `main` prior to implementing local changes or final submissions.
* **Edit Source, Not Artifacts**: Never edit build outputs or serialised states manually. Re-generate them from their original source code components.

---

## 2. State & Documentation Semantic Merging
Markdown state tracking files (`MASTER_SNAPSHOT.md`, `SESSION_STATE.md`, `ROADMAP.md`) represent the instant operational posture of SAGE. When merge conflicts occur on these files:
* **No Git conflict loop creation**: Do not commit recursive conflict markers or repeatedly loop commits trying to re-align documentation.
* **Semantic Consolidation**: Manually resolve conflict boundaries by combining unique, validated achievements and task status updates, while keeping the structural framework of the authoritative branch.
* **Single Commits**: Ensure conflict resolutions are packaged into a single clean commit with proper, git-agnostic commit headers.

---

## 3. Automated Validation
Before any PR can be merged or milestone declared complete, developers and SAGE agents **must** invoke the automated convergence script:
```bash
python scripts/verify_convergence.py
```
This script acts as the final gate, validating:
1. Ruff compliance and clean linting status.
2. Black formatting conformity.
3. 100% pytest test success (including integration and service adapters).
4. Elimination of git merge conflict patterns in `docs/master/`.
5. Local repository cleanliness.
