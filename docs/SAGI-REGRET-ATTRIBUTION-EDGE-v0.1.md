# SAGI Regret Attribution Edge v0.1

## Mission
Connect validated decision autopsy evidence to a governed regret signal that can distinguish avoidable decision error from variance and other causal conditions.

## Jigsaw edge

`DECISION → OUTCOME → AUTOPSY → COUNTERFACTUAL → LEARNING → METACOGNITION → REGRET/ATTRIBUTION`

## Capability delta

**Before:** SAGE can classify decision quality, outcome quality, and causal attribution in the decision-autopsy seam, but the resulting regret signal is not represented as a reusable typed learning artifact.

**After:** `RegretRecord` and `RegretAttributionEngine` derive a deterministic, immutable regret classification and bounded learning signal from an existing `DecisionAutopsy`.

## Attribution classes

- `DECISION_ERROR` → avoidable decision regret and heuristic review.
- `VARIANCE` → preserve policy; update variance memory.
- `INFORMATION_SHOCK` → update information requirements.
- `ENVIRONMENT_SHIFT` → update environment model.
- `COORDINATION_FAILURE` → update coordination boundary.
- `CONSTRAINT_FAILURE` → update constraint model.
- `INSUFFICIENT_EVIDENCE` → raise evidence threshold.
- `UNKNOWN` → retain uncertainty and request evidence.

Zero regret is represented as `NO_REGRET` rather than inventing a failure.

## Governance boundary

This seam does not execute actions, grant authority, capture private chain-of-thought, simulate emotion, or claim consciousness. It produces a candidate learning signal only. Promotion into canonical knowledge remains a separate validation/archive decision.

Sports remain paper-only; no wagering execution is introduced.

## Verification gate

Promotion requires focused tests plus exact-head remote CI, review, and merge. Passing implementation tests demonstrate the seam's behavior, not real-world decision improvement. Real-world capability claims require out-of-sample evidence.
