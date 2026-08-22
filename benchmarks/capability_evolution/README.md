# SAGE Capability Evolution Benchmark

**Status:** Research / benchmark harness — not a production authority.

## Purpose

Measure whether governed five-front capability evolution improves useful system growth under controlled, equal constraints. This benchmark does **not** claim SAGE is superior to every online agent framework. It establishes a reproducible mechanism-level comparison first; framework integrations are a later benchmark layer.

## Core question

Given the same starting state, five consequential opportunities, budget, dependency graph, and injected failures, does the SAGE-style loop:

`BOUND → PARALLEL FLIGHTS → EVIDENCE → RECONVERGENCE → REMEMBER → SELECT`

produce better capability evolution than sequential work, ungoverned parallel work, or dependency-aware orchestration without capability governance?

## Five flights

- **H1 Historical Recovery** — recover valuable prior concepts without rebuilding closed work.
- **H2 Implementation Reconciliation** — identify existing implementations and avoid duplicate construction.
- **H3 Impact Closure** — propagate dependency changes and trigger revalidation.
- **H4 Evidence Closure** — distinguish claimed completion from independently proven capability.
- **H5 Frontier Expansion** — select the highest-value remaining consequential frontier.

Each flight receives the same scenario state and bounded work budget. The flights are independent execution surfaces; the benchmark's shared ledger is the evidence fabric, not shared authority.

**Terminology lock:** an unqualified **flight** means the complete H1–H5 five-hitter wave. An individual path is a **hitter/front**. **Fly** means launch the complete five-hitter wave.

## Comparison policies

1. **SEQUENTIAL** — one worker processes opportunities in sequence.
2. **PARALLEL_UNGOVERNED** — five workers act concurrently without a shared capability/evidence ledger.
3. **DEPENDENCY_AWARE** — parallel workers honor declared dependencies but do not enforce capability/evidence lifecycle gates.
4. **SAGE_GOVERNED** — five bounded hitters, explicit dependencies, evidence requirements, negative knowledge retention, duplicate suppression, fail-closed reconvergence, and frontier selection.

These are controlled policies, not claims about any vendor implementation. A later adapter layer may run equivalent scenarios through LangGraph, CrewAI, Microsoft Agent Framework, Google ADK, OpenAI Agents SDK, or other systems.

## Primary metrics

1. Capability gain
2. Time to useful improvement
3. Duplicate work avoided
4. Evidence coverage
5. Failure retention
6. Recovery quality
7. Dependency awareness
8. Regression rate
9. Human intervention required
10. Next-frontier quality
11. Parallelism efficiency
12. Provenance completeness

## Validity rules

- Same scenario seeds and five opportunities for every policy.
- Same work/token-equivalent budget model.
- No cross-trial mutable state.
- Deterministic graders for mechanism metrics.
- Negative results are retained, never silently discarded.
- A green CI run does not promote benchmark conclusions into the Master Archive.
- Benchmark results remain research evidence until independently reviewed.

## Interpretation

The first release is a **mechanism benchmark**. It can establish whether the governance/control policy itself improves outcomes in a controlled environment. It cannot establish that SAGE is universally superior, nor can it replace live framework comparisons. Those require matched adapters, model/tool budgets, repeated trials, confidence intervals, and transcript/outcome review.
