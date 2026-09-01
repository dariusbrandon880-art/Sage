# SAGI Decision Autopsy Edge v0.1

**Status:** PROPOSED capability implementation pending validation.

## Jigsaw edge

`DECISION → OUTCOME → AUTOPSY → COUNTERFACTUAL → LEARNING`

This is the first implementation edge selected from the Jigsaw whole-organism architecture. The goal is not to make SAGE imitate human emotion or behavior. The goal is to make decision experience reusable: preserve the state that existed when a decision was made, evaluate what happened later, compare credible alternatives using only that state, and produce a bounded learning candidate.

## Capability delta

**Before**

SAGE has decision, prediction, evaluation, and failure-diagnostic surfaces, but no single governed reusable projection that separates decision quality from outcome quality while enforcing a decision-time information boundary for counterfactual analysis.

**After**

`DecisionAutopsyEngine` can:

1. bind an outcome to its exact decision;
2. reject impossible chronology;
3. require every credible decision-time alternative to be represented;
4. require counterfactuals to use the exact decision-time information snapshot and cutoff;
5. compare chosen expected utility with the best alternative;
6. classify decision quality separately from observed outcome quality;
7. compute decision regret without treating a bad outcome as proof of a bad decision;
8. classify default good-decision/bad-outcome cases as variance and bad-decision/good-outcome cases as decision error;
9. preserve an explicit lesson as a learning candidate without automatic promotion.

## Why this matters to the organism

This edge connects the existing organism loop beyond one-shot prediction:

`SENSE → BOUND → MODEL → DECIDE → ACT/OBSERVE → AUTOPSY → COUNTERFACTUAL → REGRET → LEARN → VERIFY → MEMORY → SELF-MODEL`

The implementation is intentionally a pure projection. Persistence, canonical promotion, autonomous authority, and action execution remain outside this module.

## Anti-hindsight contract

A counterfactual is admissible only when:

- its action is one of the alternatives recorded before the decision;
- its information snapshot hash exactly matches the decision record;
- its information cutoff exactly equals the decision timestamp;
- it does not depend on the observed outcome to redefine the pre-decision state.

This makes hindsight contamination a testable failure rather than an informal warning.

## Evidence model

The autopsy preserves four separate signals:

- **Decision quality:** was the chosen path reasonable relative to the alternatives available then?
- **Outcome quality:** was the realized result above or below the chosen expectation?
- **Attribution:** what evidence-supported explanation best fits the result?
- **Regret:** how much expected utility was left on the table relative to the best recorded alternative?

These signals must not be collapsed into a single win/loss label.

## Governance boundary

- No consciousness claim.
- No synthetic emotion or deliberate human-like error.
- No authority expansion.
- No private chain-of-thought capture.
- No automatic Master Archive promotion.
- Sports research remains paper-only; `wagering_executed=False` remains mandatory.

## Gate

Promotion requires:

`EXACT START HEAD → IMPLEMENTATION → FOCUSED TESTS → ADVERSARIAL TESTS → REMOTE EXACT-HEAD CI → REVIEW → MERGE → RECONVERGENCE`

A passing test suite proves the seam behaves as coded. It does not by itself prove that the learning candidate improves real-world decisions; that requires later out-of-sample evidence.
