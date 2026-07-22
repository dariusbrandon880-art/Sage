# ADR-003: SAGE Merge Convergence Policy

- **Status**: APPROVED / ACTIVE
- **Date**: 2026-07-22
- **Deciders**: SAGE Development Team

---

## 1. Context
SAGE operates as an autonomous, continuous-development platform. During parallel agent or human development sessions, multiple branches may remain active over extended periods. Because the SAGE runtime updates key operational state documents (`docs/master/MASTER_SNAPSHOT.md` and `docs/master/SESSION_STATE.md`) upon every milestone completion, branches frequently diverge and modify the same operational state lines.

Previously, this has resulted in:
- Complex recursive merge conflict loops.
- Obsolete or duplicated historical state replay.
- Wasted resource cycles spent resolving document-only merge conflicts instead of advancing features.

---

## 2. Decision
We establish a permanent, canonical **Merge Convergence Policy** to govern all repository operations. The core decisions are:
1. **Absolute Authoritativeness**: The latest version of the `main` branch is the absolute single source of truth.
2. **Mandatory Sync & Rebase**: Developers and autonomous agents must fetch and rebase active work on `main` prior to initiating any major implementation.
3. **No Recursive Operational Document Merging**: Operational documents (`docs/master/MASTER_SNAPSHOT.md` and `docs/master/SESSION_STATE.md`) always converge to the latest validated `main` version. Only newly validated, active session status is applied on top of the `main` version.
4. **Circut-Breaker Re-Branching**: If sync/merge loops persist, agents must discard obsolete merge history, branch a clean baseline from `main`, and replay only the relevant validated implementation commits.
5. **Continuous Verification Tooling**: To enforce this workflow, we implement an automated validation utility (`scripts/verify_convergence.py`) that checks environment, test suites, styling, and documentation/archive integrity.

---

## 3. Consequences
- **Positive**:
  - Permanently eliminates recursive documentation merge conflict loops.
  - Ensures a clean, readable git commit history without noise.
  - Automates and accelerates the synchronization check process for both agents and human developers.
- **Negative**:
  - Requires developers to maintain discipline with git rebase and clean commit histories.
  - Discards intermediate development merge artifacts in favor of clean baselines.

---

## 4. References
- Detailed Policy: [docs/master/MERGE_CONVERGENCE_POLICY.md](../../docs/master/MERGE_CONVERGENCE_POLICY.md)
