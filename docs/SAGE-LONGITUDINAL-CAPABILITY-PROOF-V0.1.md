# SAGE Longitudinal Capability Proof v0.1

## Purpose

Convert the Inventor Stage operating hypothesis into a governed experiment that can distinguish architecture claims from demonstrated long-horizon capability.

## Locked causal chain

DOCTRINE → IMPLEMENTATION → FLIGHT → MEASUREMENT → INDEPENDENT VERIFICATION → COMPOUND

The experiment is itself governed. The mission set, baseline, thresholds, and verdict rules are fixed before observations are interpreted.

## Existing SAGE primitives reused

- `sage/experimental/flight_record.py` remains the durable flight/evidence path.
- `sage/experimental/progression.py` remains the mission progression and receipt path.
- Existing attestation/provenance mechanisms remain authoritative.
- The new evaluator is experimental and does not create a second authority or persistence system.

## Pre-registration rules

1. A `MissionCase` set is fixed before evaluation.
2. Baseline and SAGE must execute the same mission IDs.
3. Missing, duplicate, extra, or mislabeled observations fail closed before a verdict.
4. The evaluation can be finalized only once.
5. The plan is canonically hashed before comparison.
6. Positive capability requires beating the baseline by the registered relative-gain threshold.
7. Positive capability also requires complete evidence, provenance preservation, blocked unauthorized transitions, continuity integrity, cross-session capability retention, and sufficiently supported learning candidates.
8. Contradiction, regression, or continuity/provenance failure cannot produce a positive verdict.
9. Missing learning-quality evidence is `HOLD`, never positive evidence.
10. Timing and cost are recorded as observed metrics; they are not silently converted into optimization claims without a registered threshold.

## Longitudinal measurements

The evaluator records:

- success rate
- relative improvement over baseline
- recovery rate
- regression rate
- evidence completeness
- provenance preservation
- unauthorized-transition blocking
- continuity integrity
- capability retention across sessions
- learning-candidate quality
- mean elapsed time
- mean cost units

## Verdict semantics

`PASS` means the registered positive capability conditions survived the evaluation.

`HOLD` means the evidence is insufficient or indeterminate for a positive capability claim.

`NEGATIVE_RESULT` means the run demonstrated a material failure such as regression, continuity loss, retention loss, or provenance loss.

`INDETERMINATE` remains reserved for future explicit uncertainty states; it is not a positive result.

## Flight boundary

The current implementation establishes the measurement and verdict substrate. It does **not** manufacture a SAGE capability result from fixtures. A real capability verdict requires actual baseline and SAGE observations from the same locked mission set, followed by independent inspection of the resulting flight records and receipts.

## External challenge incorporated

Current 2026 research independently reinforces the need for controlled longitudinal evaluation. Continual Learning Bench evaluates improvement through sequential experience and isolates learning from prior capability; AMA-Bench evaluates long-horizon memory over agent trajectories; and recent lifespan work argues that deployed-agent reliability is a longitudinal property rather than a day-one benchmark property.

SAGE therefore treats longitudinal flight evidence, not a single green test run, as the proof boundary.

## STOP boundary

Do not add a new benchmark family, new authority layer, new persistence layer, or speculative scoring dimension in this frontier. The next step is execution of the locked mission set, collection of real observations, independent verification, and only then compound or retain the negative result.
