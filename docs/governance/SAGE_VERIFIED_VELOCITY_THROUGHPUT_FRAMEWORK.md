# SAGE Verified Velocity Throughput Framework

**Status:** Governance / Evaluation Framework  
**Purpose:** Establish a durable measurement contract for determining whether SAGE increases verified capability throughput under fixed external agent capacity.

## 1. Strategic thesis

SAGE should not claim a productivity multiplier because it can create more parallel tasks. The claim worth proving is stronger:

> **SAGE increases verified engineering capability produced per unit of scarce external agent capacity while preserving correctness, governance, and reconvergence integrity.**

The Big Jump Wave is therefore an experimental instrument for measuring system-level velocity, not merely task fan-out.

## 2. Core measurement

The primary metric is:

**Verified Capability Throughput = verified capability units / agent-capacity-hour**

A capability unit must be defined before a benchmark run and must satisfy the SAGE completion boundary:

**Build + Verification + Evidence + Reusable capability**

Raw task count, generated code volume, or parallel worker count is not sufficient evidence of velocity gain.

## 3. Controlled comparison

Every velocity claim should compare a SAGE wave against a credible sequential or otherwise capacity-matched baseline.

Capture, at minimum:

| Metric | Required observation |
|---|---|
| External agent sessions | Number actually available/consumed |
| Missions attempted | Work units admitted |
| Flights executed | Bounded internal work units |
| Genuine overlap | Timestamp/thread/process evidence |
| Verified completions | Capability units passing acceptance |
| Regression outcome | Full relevant test boundary |
| Human intervention | Material interventions required |
| Wall-clock duration | Start/end timestamps |
| Agent-capacity-hours | External capacity consumed |
| Verified capability throughput | Primary derived metric |
| Reconciliation cost | Merge/conflict/rework burden |

## 4. Big Jump Wave relationship

The canonical five-flight wave provides the bounded internal execution layer. The 15-flight SAGI experiment provides a three-session × five-flight fan-out model when three external sessions are actually available.

These are **execution structures**, not automatically three or fifteen independent externally billable agent tasks. Product/provider limits must remain separate from SAGE's internal decomposition.

The system must distinguish:

1. external capacity;
2. internal flight concurrency;
3. completed capability;
4. verified capability;
5. economic throughput.

## 5. Evidence contract

A velocity result is admissible only when the evidence is bound to the exact execution state and independently reconcilable.

Required evidence should include, where applicable:

- exact execution commit SHA;
- identity-addressed wave receipts;
- deterministic receipt hashes;
- per-flight execution records;
- concurrency overlap proof;
- advancement matrix results;
- dedicated tests;
- full regression results;
- remote CI results on the final published commit;
- reconciliation/merge outcome.

Evidence generated locally but not published, or evidence bound to an earlier commit, is **not** final evidence.

## 6. Velocity multiplier

When a capacity-matched baseline exists, calculate:

**Velocity Multiplier = SAGE verified-capability throughput / baseline verified-capability throughput**

Do not report a multiplier from elapsed time alone. A shorter run with lower verified output, higher intervention, or higher regression/rework cost does not establish a durable gain.

For client-facing evaluation, also track:

**Net Verified Throughput = verified capability value − material rework/intervention cost**

The exact economic conversion should be defined per workload rather than invented globally.

## 7. Repeated-wave requirement

One successful Big Jump Wave demonstrates that the mechanism can work. It does **not** establish a general productivity multiplier.

A stronger claim requires repeated, comparable waves across representative workloads with preserved verification and reconciliation boundaries.

At minimum, future evaluations should preserve:

- fixed or explicitly documented external capacity;
- predeclared capability-unit definitions;
- comparable baseline workloads;
- identical acceptance criteria;
- complete evidence capture;
- recorded failures and rework, not just successes.

## 8. Governance rule

C2 must treat velocity as a measured system property.

**Never optimize the metric by weakening the verification boundary.**

Parallelism is valuable only when it compounds into verified, reusable capability without proportionally increasing defects, reconciliation burden, or operator intervention.

## 9. Productization implication

If repeated controlled evaluations establish a durable positive multiplier, SAGE may treat **verified capability throughput under constrained agent capacity** as a product-value claim and client evaluation axis.

Until repeated evidence establishes the multiplier, language must remain experimental:

- **Proven:** observed execution behavior and measured results.
- **Supported:** repeatable evidence across multiple controlled runs.
- **Hypothesis:** expected economic/productivity advantage not yet sufficiently demonstrated.

This distinction protects both technical credibility and commercial trust.

## 10. Canonical loop

```text
SENSE
  ↓
BOUND WORK
  ↓
PARALLELIZE
  ↓
EXECUTE
  ↓
VERIFY
  ↓
RECONVERGE
  ↓
MEASURE VERIFIED OUTPUT
  ↓
COMPARE AGAINST BASELINE
  ↓
LEARN / IMPROVE
```

The strategic objective is not maximum concurrency. It is **maximum trustworthy capability throughput per scarce unit of external capacity**.

## 11. Relationship to existing SAGE architecture

This framework extends, rather than replaces, the existing Big Jump Wave, C2 flight-control, workflow-velocity, multi-frontier dispatch, evidence-capture, and organism/jigsaw governance surfaces. The existing architecture supplies the execution and verification machinery; this document establishes the measurement contract needed to determine whether that machinery creates economically meaningful velocity.
