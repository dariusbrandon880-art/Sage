# SAGE Archaeological Jigsaw Reconciliation — 2026-08-22

**Classification:** Governed reconciliation record
**Status:** ACTIVE — first-pass inventory
**Authority:** Master Archive remains canonical; this record is an analytical projection until validated/promoted.

## Purpose

Reconcile SAGE's accumulated architecture, roadmaps, research, capability records, continuity projections, implementation, and evidence without creating a second source of truth.

## Authority Model

1. **Master Archive / Constitution:** constitutional and canonical knowledge authority.
2. **Git implementation:** observable implementation truth.
3. **Tests / CI / receipts / evidence:** verification truth for claims about behavior.
4. **Research / experimental documents:** candidate knowledge unless explicitly validated and promoted.
5. **Historical reports:** lineage/context; they do not override current implementation or evidence.

## First-Pass Reconciliation Findings

### A. Constitutional layer — VALIDATED / KEEP

`docs/master/CONSTITUTION.md` explicitly establishes knowledge persistence, validation-before-expansion, evidence symmetry, confidence honesty, and evolution without destruction. It also defines ACR/CIV, SKAL/HSI/KL/SAGE-X, governed knowledge promotion, memory stratification, and the no-drift/no-duplicate/no-validation-bypass rules.

**Disposition:** preserve. Use as constitutional constraint, not as a current engineering backlog.

### B. Main Archive index — VALIDATED STRUCTURE / REQUIRES PROJECTION AUDIT

`Main Archive/INDEX.md` defines lifecycle states (`PROPOSED → VALIDATED → ARCHIVE_CANDIDATE → CANONICAL`) and contains many canonical/validated/proposed records. It is useful as an inventory but contains historical and strategic projections alongside current engineering records.

**Disposition:** inventory authority, not behavioral authority. Every consequential entry must reconcile against current implementation/evidence before reuse.

### C. Legacy strategic roadmap — STALE/CONFLICTING VIEW

`Main Archive/architecture/roadmap.md` describes ACR, capability registry, intelligence, automation, external interfaces, and business/application layers. It also describes older connector/client assumptions.

**Disposition:** retain as architectural lineage. Do not treat its ACTIVE labels or implementation details as current without implementation/evidence verification.

### D. Master roadmap — STALE/CONFLICTING VIEW

`docs/master/ROADMAP.md` contains the SAGE 2 unified architecture and older milestone claims, including completed live ecosystem milestones and a future v3 distributed collaborative mind.

**Disposition:** retain historical continuity. Its milestone labels require current evidence reconciliation before being used for frontier selection.

### E. Capability Tree Health Assessment — VALIDATED HISTORICAL ASSESSMENT / RECONCILIATION INPUT

`docs/SAGE-CAPABILITY-TREE-HEALTH-ASSESSMENT-REPORT.md` documents the production/experimental boundary, ACT milestones, evidence chain, duplicated state/signature concepts, unresolved research questions, maturity classifications, and the proposed Milestone 5 controlled rehydration direction.

Important reusable unresolved questions include multi-session lineage integrity, decentralized signed rehydration, nonce replay prevention, and dynamic trust negotiation.

**Disposition:** preserve as validated assessment; re-check each maturity label against current implementation before promotion or build selection.

### F. Current five-flight architecture — ACTIVE BUILD / CURRENT OPERATIONAL FRONTIER

The current five-capability wave and its fail-closed reconvergence machinery are current execution infrastructure. Run #714 established a green five-flight execution boundary for the current wave.

**Disposition:** active operational mechanism. The five execution slots are reusable mission hitters and should not be permanently bound to historical subsystem names.

### G. Capability Evolution Governance Framework — ACTIVE GOVERNANCE CANDIDATE

The framework now establishes multi-axis continuous capability growth, incompletion as first-class state, evidence-bound lifecycle transitions, fail-closed reconvergence, and a full-system jigsaw audit contract.

**Disposition:** candidate governance record pending normal validation/promotion. It must not silently become constitutional authority merely because CI is green.

## Cross-System Jigsaw Model

Every consequential SAGE claim should be traceable as:

`claim → artifact → implementation → dependency → execution → evidence → verification → lifecycle state → archive disposition`

A duplicated claim is not a duplicated capability. Multiple documents may be projections of one capability. Conversely, one capability may have multiple disconnected evidence or dependency paths that must be reconciled.

## Initial Conflict Classes

1. **Projection drift:** older roadmaps describe ACTIVE/COMPLETE states that may no longer match current implementation.
2. **Vocabulary drift:** historical architecture names and current capability names coexist.
3. **Evidence-age drift:** historical validation counts and baselines are preserved but may be superseded by current CI.
4. **Authority ambiguity risk:** documents can describe governance but cannot replace the Master Archive or current evidence.
5. **Capability duplication risk:** multiple schemas/registries may represent overlapping state, lineage, or provenance concepts.
6. **Incomplete-state loss risk:** old documents frequently use binary COMPLETE/FUTURE framing where the current governance model requires explicit incomplete/blocked/negative states.

## Five-Hitter Exploitation Rule

For each governed growth wave, select up to five independently bounded consequential targets from the reconciled frontier. Each hitter may perform implementation, integration, validation, falsification, dependency closure, or evidence hardening. All five may advance simultaneously when their boundaries are independent.

Parallel execution does not merge authority. Each target retains its own provenance, evidence, lifecycle state, and verification result. Wave qualification remains fail-closed.

## Next Reconciliation Pass

The next pass must inspect, piece by piece:

- canonical architecture/ADRs;
- implementation modules corresponding to each claimed capability;
- current tests and CI evidence;
- continuity/control-tower records;
- cognitive/PFC records;
- research/experimental candidates;
- ACT/ACR lineage and rehydration work;
- evidence/receipt schemas;
- failure/negative knowledge;
- current frontier/projection files.

Each item will receive exactly one working disposition: `VALIDATED/KEEP`, `ACTIVE BUILD`, `READY FRONTIER`, `RESEARCH CANDIDATE`, `DEPENDENCY`, `NEGATIVE/CLOSED`, or `STALE/CONFLICTING`.

No architecture is declared complete from documentation alone. No closed finding is reopened without new evidence. No new lane is created by this reconciliation.
