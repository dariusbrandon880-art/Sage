# Sports Quant Recon — Observation 006

**Title:** Jigsaw whole-organism / human-intelligence substrate
**Date:** 2026-09-01
**Status:** Non-canonical research evidence; architecture candidate
**Boundary:** `wagering_executed = False`

## 1. Raw signal

The supplied Intetics article (2018) is historical/speculative material. Its useful signal is that pattern recognition and narrow task automation do not by themselves explain the broader contextual, reflective, creative, common-sense, and adaptive functions associated with human expertise.

The stronger synthesis from the accompanying research surfaces is a candidate set of mechanisms:

- metacognition and uncertainty awareness;
- self-monitoring;
- decision-state memory;
- counterfactual reasoning;
- regret-style learning;
- variance attribution;
- experience memory;
- curiosity/question generation;
- contextual intuition as compressed prior experience;
- common-sense consequence modeling;
- operational self-modeling.

These are architectural hypotheses, not evidence that SAGE is conscious.

## 2. C2 synthesis — do not build human theater

The target is not to make SAGE pretend to have human emotions.

The target is to reproduce useful **functions of human intelligence**:

> What did I know? What did I believe? What did I choose? Why? How uncertain was I? What happened? Was the decision actually good? What alternatives existed at the time? Why did the outcome occur? What should change? What remains unknown?

Reject fake hesitation, deliberate mistakes, arbitrary randomness, and simulated emotion as substitutes for intelligence.

## 3. Jigsaw whole-organism principle

SAGE/SAGI should be treated as a **jigsaw organism**.

Every capability is a piece with:

`identity + purpose + interfaces + dependencies + provenance + lifecycle + temporal semantics + authority boundary + failure modes + evidence requirements + learning interface + verification interface`

The edges between pieces are first-class architecture.

Candidate closed-loop composition:

`RECON → CONTEXT → REASONING → METACOGNITION → DECISION → ACTION → OBSERVATION → AUTOPSY → COUNTERFACTUAL → REGRET → LEARNING → MEMORY → SELF-MODEL → CURIOSITY → RECON`

The existing Capability Graph becomes the **jigsaw board**: not merely an inventory of modules, but the substrate for finding missing pieces, weak edges, integration gaps, and the smallest high-leverage capability delta.

## 4. Decision quality ≠ outcome quality

The organism must not learn directly from outcome labels alone.

At minimum it must distinguish:

| Decision | Outcome | Interpretation |
|---|---|---|
| Good | Good | successful decision |
| Good | Bad | variance/environment/information-shock candidate |
| Bad | Good | false success / lucky outcome candidate |
| Bad | Bad | genuine decision failure |
| Unknown | Any | insufficient evidence |

A loss is not automatically a bad decision. A win is not automatically proof of competence.

## 5. Decision Autopsy candidate

```text
DECISION_ID
CONTEXT_STATE
INFORMATION_AVAILABLE_AT_T0
ASSUMPTIONS
BELIEF_STATE
OPTIONS_CONSIDERED
CHOSEN_ACTION
CONFIDENCE
RISK_ASSESSMENT
OBSERVED_EFFECT
OUTCOME
COUNTERFACTUAL_OPTIONS
COUNTERFACTUAL_OUTCOMES
DECISION_QUALITY
OUTCOME_QUALITY
VARIANCE_ATTRIBUTION
REGRET
CAUSAL_HYPOTHESES
FAILURE_CLASS
LESSON_CANDIDATE
REQUIRED_VERIFICATION
MEMORY_UPDATE_CANDIDATE
```

Point-in-time state is mandatory. Later information must never be allowed to leak backward into the historical decision state.

## 6. Metacognitive candidate

A single confidence field is insufficient. Candidate dimensions:

1. knowledge confidence;
2. inference confidence;
3. decision confidence;
4. outcome-attribution confidence;
5. historical calibration;
6. evidence conflict;
7. material unknowns.

Metacognition must affect behavior. Uncertainty may trigger additional recon, narrower claims, safer bounded actions, or fail-closed STOP behavior.

## 7. Counterfactual + regret candidate

Preserve credible alternatives to the chosen action.

```text
ACTUAL:
T0 → A → T1 → B → OUTCOME

COUNTERFACTUALS:
T0 → A' → ...
T0 → C  → ...
T0 → D  → ...
```

Counterfactuals remain hypotheses unless supported by observed alternative runs or a validated model.

Regret is not punishment. It is a structured comparison between the chosen action and credible alternatives under the information available at decision time.

## 8. Variance / luck attribution

The organism needs an attribution layer that asks whether outcome deviation came from:

- decision error;
- execution error;
- environmental change;
- information shock;
- stochastic variance;
- model misspecification;
- missing information;
- unresolved causal uncertainty.

This prevents false learning from both lucky wins and unlucky losses.

## 9. Operational self-model

A bounded self-model is useful without claiming consciousness.

Candidate fields:

`CURRENT_MISSION + ACTIVE_GOALS + KNOWN_CAPABILITIES + DEGRADED_CAPABILITIES + KNOWN_LIMITS + MATERIAL_UNKNOWNS + CURRENT_ASSUMPTIONS + CONFIDENCE + RECENT_FAILURES + RECENT_RECOVERIES + CALIBRATION + AVAILABLE_TOOLS + AUTHORITY_BOUNDARIES + SECURITY_BOUNDARIES + OPEN_QUESTIONS + NEXT_INFORMATION_NEEDS`

The self-model is a projection of validated evidence. It grants no authority.

## 10. Sports as proving ground

Issue #365 remains the active Sports/SAGI paper-decision frontier.

Sports already exposes useful primitives for testing this organism model:

`SPORT OBSERVATION → MARKET STATE → MODEL STATE → DECISION STATE → TEMPORAL LOCK → OUTCOME → AUTOPSY → COUNTERFACTUAL → CALIBRATION → REGRET/FAILURE LEARNING → OOS VALIDATION`

This makes Sports a bounded proving ground for whole-organism learning rather than a separate betting island.

No real-money execution, staking, wallet/payment automation, or sportsbook authentication is part of the architecture.

## 11. Dynamic Five-Flight jigsaw model

F1–F5 remain anonymous reusable execution slots.

Each Big Jump Wave should use the Capability Graph to identify distinct missing pieces or edges and dynamically assign the slots:

```text
CAPABILITY GRAPH
      ↓
MISSING PIECES / WEAK EDGES
      ↓
DYNAMIC F1–F5 MISSION ASSIGNMENT
      ↓
PARALLEL FULL-STACK EXECUTION
      ↓
VALIDATED SHARED LEARNING
      ↓
C2 RECONVERGENCE
```

A flight can research, recon, build, repair, verify, integrate, or produce evidence. Mission identity belongs to the mission, never to the flight number.

## 12. Falsification program

The architecture remains a hypothesis until evidence answers:

1. Does decision-state memory improve outcome attribution?
2. Do counterfactuals reduce false learning from lucky wins/losses?
3. Does calibrated metacognition improve decisions under uncertainty?
4. Does a self-model improve recovery from degraded capability?
5. Does experience memory improve transfer across missions?
6. Does curiosity-driven information acquisition improve decisions enough to justify cost?
7. Does graph-edge verification reduce integration failures?
8. Does shared validated learning increase capability without increasing drift or contamination?
9. Can the same organism substrate serve multiple domains without permanent flight identities?
10. Can Sports validate the temporal/decision/outcome learning chain under paper-only constraints?

Negative results are retained as organism immune memory.

## 13. Proposed first engineering vertical

**Decision Experience Loop v0.1**

Before:

> SAGE can record what happened but cannot reliably reconstruct the decision state, distinguish decision quality from outcome quality, preserve credible alternatives, and produce a point-in-time learning candidate.

After:

> SAGE can reconstruct the decision state, evaluate outcome attribution, preserve counterfactual candidates, estimate bounded regret, generate a governed learning candidate, and verify that the learning did not use future information.

This is the first concrete candidate because it connects existing evidence, observation, learning, verification, and sports temporal infrastructure into one organism edge chain.

## 14. Repository architecture record

The complete cross-organism architecture is recorded in:

`docs/SAGI-JIGSAW-WHOLE-ORGANISM-ARCHITECTURE.md`

That record defines the organism composition, jigsaw contracts, Capability Graph integration, dynamic Five-Flight model, shared learning flow, maturity ladder, falsification requirements, and governance boundaries.

## 15. Lock

> **Do not ask which module should become smarter in isolation. Ask which missing piece or missing edge prevents the organism from behaving better as a whole.**

**Pieces create capability. Connections create the organism. Governance keeps the organism trustworthy.**
