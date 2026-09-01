# SAGI Metacognition & Decision Autopsy Edge v0.1

**Status:** Proposed experimental capability pending validation.

## Jigsaw edge

`DECISION → OUTCOME → AUTOPSY → COUNTERFACTUAL → LEARNING → METACOGNITION`

This edge adds explicit, auditable self-monitoring signals to the decision-autopsy substrate. It does not claim consciousness or simulate human emotion.

## Capability delta

**Before:** decision autopsy can separate decision quality from outcome quality, but confidence, uncertainty, degradation, and risk regulation are not represented as a reusable metacognitive state.

**After:** `MetacognitiveState` preserves explicit knowledge, inference, decision, and outcome confidence; risk tolerance and assessed risk; calibration error; unknowns; assumptions; and degradation state. `MetacognitiveEngine` converts those signals into a bounded review requirement without executing actions or granting authority.

## Contract

- State is immutable.
- Confidence values are bounded to `[0, 1]`.
- Unknowns and assumptions are explicit and unique.
- Composite confidence is conservative and cannot exceed the weakest core confidence dimension.
- Risk above tolerance forces review.
- Degradation or unresolved unknowns force review.
- Outcome updates produce a new state rather than mutating the prior snapshot.
- No private chain-of-thought capture.
- No synthetic emotion or deliberate errors.
- No authority expansion or autonomous action execution.
- Sports research remains paper-only; `wagering_executed=False` remains mandatory.

## Integration target

The intended organism flow becomes:

`SENSE → BOUND → MODEL → METACOGNITION → DECIDE → ACT/OBSERVE → AUTOPSY → COUNTERFACTUAL → REGRET → LEARN → VERIFY → MEMORY → SELF-MODEL`

This is an architecture candidate. Passing tests establish implementation behavior, not demonstrated real-world decision improvement. Promotion requires exact-head remote CI, review, merge, and later out-of-sample evidence.
