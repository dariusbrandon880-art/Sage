# ADR-003: Merge Convergence Policy and Automated Quality Gates

## Context and Problem Statement
In high-velocity development pipelines where multiple human engineers and AI models contribute simultaneously to SAGE, keeping canonical state documents (such as `MASTER_SNAPSHOT.md` and `SESSION_STATE.md`) in continuous alignment can introduce document conflict loops and outdated version assumptions. SAGE needs a permanent, automated gate to validate merge convergence before milestones are archived.

---

## Decision
We establish a permanent **Merge Convergence Policy** and associated verification tooling to prevent loop conflicts, maintain document consistency, and preserve a strictly clean master repository root.

1. **Semantic Merging**: Define a standard merge convention treating the `main` branch as authoritative, requiring developers/agents to manually consolidate achievements instead of relying on recursive Git conflict merges on state files.
2. **Automated Verification Script (`scripts/verify_convergence.py`)**: Implement a unified diagnostic check encompassing:
   - Ruff linting.
   - Black formatting.
   - Pytest execution.
   - Merge conflict syntax checks inside docs.
   - Repository root path audits.
3. **Formal Policy (`docs/master/MERGE_CONVERGENCE_POLICY.md`)**: Publish explicit procedural instructions.

---

## Rationale
Enforcing automated gates at pre-commit and post-merge stages guarantees that no corrupted documentation or broken format styles enter the authoritative repository branch, ensuring 100% portability and continuous self-rehydration.
