# SAGE Evolution Loop v1

**Status:** Experimental / bounded implementation
**Authority:** C2 evaluation surface; no autonomous promotion authority

## Purpose

Connect SAGE's existing experience, experimentation, evidence, validation, and capability-warehouse concepts into a measurable loop. The loop evaluates operating techniques against a declared baseline and produces a recommendation. It does not promote capabilities or modify production state.

## Controlled cycle

```text
LOCK
  -> BASELINE
  -> MISSION
  -> EXECUTE
  -> OBSERVE
  -> CAPTURE EXPERIENCE
  -> GENERATE HYPOTHESES
  -> RUN COMPETING TECHNIQUES
  -> REPLICATE
  -> ADVERSARIAL CHALLENGE
  -> VALIDATE
  -> FITNESS COMPARISON
  -> PROMOTE CANDIDATE / HOLD
  -> HUMAN AUTHORIZATION
  -> WAREHOUSE
  -> REGRESSION MONITORING
  -> REUSE
```

## Fitness vector

The first implementation records seven normalized dimensions:

- mission value
- correctness
- repeatability
- evidence quality
- recovery
- generalization
- cost

A scalar score is available for ranking, but the vector remains the evidence-bearing object. A high task-completion rate cannot override weak evidence, poor recovery, regression, or excessive cost.

## Fail-closed gates

A candidate cannot receive a promotion recommendation unless it has:

1. replication evidence;
2. adversarial challenge evidence;
3. regression-free evidence;
4. a complete evidence package; and
5. human review recorded as complete.

The evaluation object exposes `promotion_authorized == False` unconditionally. `PROMOTE_CANDIDATE` means only that the measured result is eligible for an external promotion decision.

## Architectural boundary

This is intentionally a composition layer, not a new autonomous self-modification subsystem. Existing C2, Experiment Ledger, evidence capture, validation, and Capability Warehouse components remain the authoritative integration points. The next implementation phase should connect real evidence packages and repeated trials to this evaluator rather than inventing a second ledger.

## Proof target

The bounded research question is:

> Can SAGE demonstrate that a candidate operating technique is materially better than a declared baseline across repeated, adversarially challenged trials while preserving evidence integrity and governance boundaries?

A successful experiment establishes evidence for a technique, not permission for SAGE to change itself.
