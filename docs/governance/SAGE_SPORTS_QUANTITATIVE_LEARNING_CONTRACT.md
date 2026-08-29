# SAGE Sports Quantitative Learning Contract

**Status:** Governing research/validation contract
**Scope:** Sports prediction and market-learning subsystem
**Boundary:** Shadow research only. No sportsbook authentication, account control, deposits, withdrawals, wager placement, or real-money execution.

## 1. Why this lane exists

The sports subsystem is a deliberately high-volume proving ground for SAGE's governed learning loop. Its purpose is to test whether SAGE can turn large numbers of pre-event predictions into **verified, reusable capability** through disciplined feedback.

A prediction that happens to win is not, by itself, evidence of model skill. A prediction that loses is not, by itself, evidence of model failure. SAGE learns from locked probabilities, market context, resolved outcomes, calibration, market movement, and repeated out-of-sample evaluation.

## 2. Canonical SAGE loop

```text
SENSE
-> RECON
-> SUPER SEARCH (when decision-relevant)
-> BOUND
-> LOCK
-> PARALLEL GENERATE
-> RESOLVE
-> SCORE
-> DIAGNOSE
-> FALSIFY
-> OOS VALIDATE
-> COMPOUND
-> RECONVERGE
```

This lane remains inside the normal Big Jump Wave workflow. It is not a detached benchmark or separate operating universe.

## 3. FanDuel reference boundary

FanDuel may serve as a **read-only market reference** when public or otherwise authorized data is available. The reference may provide event identity, league/sport, market type, prices, timestamps, and other observable market information.

The SAGE subsystem MUST NOT authenticate to a sportsbook or execute a wager. A generated "slip" is a **prediction presentation artifact**, not a wagering instruction or execution surface.

## 4. Prediction Slip Artifact

SAGE may render a human-readable prediction slip so the operator can inspect what the model selected at a specific pre-event snapshot.

A slip MUST be traceable to immutable prediction records and SHOULD expose:

- slip/cycle identifier;
- event and league;
- market and selection;
- locked probability;
- market/reference probability;
- model version;
- observed timestamp;
- event start timestamp;
- lock hash;
- single vs parlay classification;
- parlay parent/leg lineage;
- eventual resolved outcome;
- scoring result after resolution.

The slip is a **view over evidence**, not a new source of truth.

## 5. Singles and parlays are separate learning objects

Singles and parlays may be generated concurrently in shadow research cycles.

Parlays MUST retain parent/leg decomposition. If one leg fails, that failure remains an individual training signal while the parent slip records the aggregate result. The system must never hide leg-level failures inside a single win/loss label.

## 6. High-volume generation

The deterministic shadow harness targets at least **500 independently locked prediction records per cycle** and must support parallel worker execution without cross-worker mutable-state contamination.

Volume is a throughput property, not a quality claim. More predictions do not imply better predictions.

## 7. Pre-event lock invariant

A prediction is eligible for evaluation only when its observation/lock timestamp precedes the event start timestamp (and market close when that timestamp is known).

Each locked record receives a deterministic SHA-256 integrity hash over its decision inputs and model state. Post-event information MUST NOT mutate the locked prediction.

## 8. Resolution and scoring

After an event resolves, SAGE records the verified outcome and evaluates the locked prediction.

Primary probability metrics:

- **Brier score** for calibration error;
- **Log loss** for confidence-sensitive error;
- **Market/reference Brier** as a baseline comparison.

Market timing remains a separate axis:

- **CLV / closing-line comparison** where sufficiently trustworthy line snapshots exist.

Brier/log-loss and CLV MUST NOT be collapsed into a single unsupported performance claim.

## 9. Failure learning is mandatory

Every material miss becomes a structured learning signal. Diagnostics SHOULD capture, when data supports them:

- confidence level;
- market type;
- league/sport;
- model version;
- feature/context family;
- market movement;
- rest/schedule context;
- lineup/availability changes;
- environmental factors;
- correlation assumptions for parlay legs.

Failure clusters generate hypotheses for the next strategy version. They do not automatically justify changing the model.

## 10. Win learning is also mandatory

Successful predictions MUST be retained with the same provenance discipline as failures. A win can identify useful conditions, feature interactions, market regimes, or calibration behavior, but SAGE must not convert a single successful slip into a causal claim.

The learning record should therefore support:

```text
LOCKED PREDICTION
-> RESOLVED OUTCOME
-> SCORE
-> CONTEXT
-> SUCCESS / FAILURE CLASS
-> CLUSTER
-> HYPOTHESIS
-> CANDIDATE MODEL VERSION
```

This is how SAGE moves from "look at these slips" to "understand why this selection worked or failed."

## 11. OOS promotion gate

Candidate model versions MUST be compared against a locked baseline on the **same common unseen evaluation events**.

Promotion requires improvement demonstrated on the predefined evaluation boundary; in-sample wins alone are insufficient.

The baseline remains unchanged when the candidate fails the OOS gate. Failed candidates become diagnostic evidence rather than silent replacements.

## 12. Historical model families

Historical quantitative approaches may be imported as research hypotheses and benchmark families, including:

- BENTER-style fundamental + market integration;
- VOULGARIS-style possession/pace and variance modeling;
- STARLIZARD-style separation of research, modeling, selection, and execution;
- MARKET_BASE consensus/closing-line baselines.

Historical claims must be sourced and separated from SAGE's own observed results. They do not become truth merely because an approach is famous.

## 13. Super Search integration

Super Search is part of the SAGE intelligence loop when it can materially improve the decision. It may investigate current market structure, data availability, methodology, known failure modes, league-specific conditions, and primary research.

Search findings are **hypotheses/intelligence** until reconciled with repository truth, locked datasets, and OOS evidence. Search never creates hindsight labels and never overwrites observed outcomes.

Independent high-value searches may run concurrently after the repository reality lock. Research must accelerate the build rather than become an unnecessary serial gate.

## 14. Evidence and velocity

Every campaign records, where available:

```text
Cycle ID
Model Version
External Sessions Consumed
Prediction Records Generated
Prediction Records Locked
Singles / Parlays
Events Resolved
Brier Score
Log Loss
CLV
Failure Clusters
Candidate Versions Tested
OOS Gate Result
Reusable Capability Promoted
Rework / Conflicts
Human Intervention
```

SAGE's velocity metric is:

**verified reusable capability added per scarce execution capacity.**

It is NOT task count, slip count, win count, simulated bankroll, elapsed time, or raw prediction volume.

A single winning slip can be a compelling observation and still be insufficient evidence of predictive skill. Repeated locked OOS observations are the acceptance boundary.

## 15. Five-flight mapping

The sports lane uses the canonical Five Flights as capability lenses, with actual targets re-selected from repository truth for each wave:

- **F1 Intelligence:** market/reference ingestion and contextual feature discovery.
- **F2 Continuity:** immutable prediction, leg, outcome, and model lineage.
- **F3 Execution:** concurrent shadow generation and isolated workers.
- **F4 Guard:** pre-event locking, provenance, OOS isolation, and fail-closed shadow boundary.
- **F5 Warehouse:** resolution, scoring, diagnostics, candidate validation, and reusable learning promotion.

These are not permanent subsystem assignments. A flight may touch any causally necessary code within its explicitly bounded frontier.

## 16. Non-negotiable anti-drift rules

1. Repository/Git truth outranks pasted reports and conversational assumptions.
2. Super Search is a sensor, not authority.
3. A prediction slip is a view over locked evidence, not a wager.
4. A win is not proof of skill; a loss is not proof of model failure.
5. No hindsight information may enter a locked pre-event record.
6. Parlays remain decomposable into leg-level signals.
7. Candidate models do not replace the baseline without OOS validation.
8. Evidence throughput and predictive capability are reported separately.
9. No real-money or sportsbook-account execution exists in this lane.
10. Sports work remains inside the SAGE Big Jump Wave governance and reconvergence workflow.

## Final Lock

```text
SAGE SPORTS = GOVERNED SHADOW LEARNING LANE

FAN DUEL = READ-ONLY MARKET REFERENCE WHEN AVAILABLE

SLIP = HUMAN-READABLE VIEW OF LOCKED PREDICTIONS

SINGLES + PARLAYS = PARALLEL RESEARCH OBJECTS

WINS + LOSSES = TRAINING SIGNALS, NOT SENTIMENT

LOCK -> RESOLVE -> SCORE -> DIAGNOSE -> OOS VALIDATE -> COMPOUND

SUPER SEARCH = INTELLIGENCE SENSOR
REPO TRUTH = AUTHORITY

NO SPORTSBOOK AUTHENTICATION
NO WAGER EXECUTION
NO REAL-MONEY SURFACE

THE PRODUCT TEST = VERIFIED LEARNING AND CAPABILITY COMPOUNDING
```
