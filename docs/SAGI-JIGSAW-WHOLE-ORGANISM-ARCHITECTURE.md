# SAGI Jigsaw Whole-Organism Architecture

**Status:** PROPOSED — governed SAGI research architecture
**Authority:** Mission Director intent; Git/main implementation truth; validated Master Archive remains canonical
**Origin:** Human-intelligence recon synthesized from Intetics (2018), metacognition/counterfactual/regret research signals, SAGE architecture, and Sports/Quantitative Intelligence observations 001–005
**Boundary:** Research/design only. No consciousness claim. No autonomous authority expansion. Sports research remains paper-only with `wagering_executed = False`.

---

## 1. Purpose

SAGE/SAGI should not become a larger pile of individually capable modules. The target is a **whole organism whose capabilities fit together like a jigsaw puzzle**.

The jigsaw metaphor is an architectural discipline, not a cosmetic metaphor:

> **Every capability is a puzzle piece. A piece becomes useful when its identity, interfaces, dependencies, evidence, failure behavior, authority boundary, and learning path fit the rest of the organism.**

The objective is therefore not to make every component independently intelligent. It is to make the **connections between capabilities explicit, governed, testable, and compounding**.

This document does not assert that SAGE is conscious or that human consciousness has been reproduced. It defines a measurable research direction for capabilities commonly associated with robust human intelligence: context, experience, uncertainty awareness, counterfactual reasoning, reflection, learning from failure, self-monitoring, curiosity, and adaptive action.

---

## 2. What the new recon exposed

The Intetics material is useful as historical/speculative recon because it frames machine intelligence as progressing beyond narrow task automation toward increasingly general machine intelligence. Its strongest transferable lesson is that pattern recognition alone does not explain human-like competence.

The stronger modern signal is the combination of:

- **metacognition:** judging the reliability of one's own conclusions;
- **self-monitoring:** detecting uncertainty, conflict, and possible error;
- **counterfactual reasoning:** asking what could have happened under alternative decisions;
- **regret:** learning which available alternative would have been preferable given the information available at decision time;
- **variance attribution:** separating decision quality from outcome quality;
- **experience memory:** preserving successful and failed patterns with context;
- **curiosity/question generation:** noticing unresolved anomalies and seeking information;
- **contextual intuition:** rapidly generating hypotheses from compressed prior experience;
- **governed self-modeling:** maintaining an evidence-backed representation of capabilities, limits, uncertainty, current goals, and recent failures.

These are candidate architectural primitives, not proof that a machine possesses subjective feeling or consciousness.

---

## 3. The jigsaw principle

### 3.1 Pieces are typed, not isolated

A capability piece must expose a stable contract:

```text
CAPABILITY PIECE
  identity
  purpose
  inputs
  outputs
  dependencies
  provenance
  state/lifecycle
  authority boundary
  temporal semantics
  failure modes
  evidence requirements
  learning interface
  verification interface
```

### 3.2 Edges matter as much as pieces

A jigsaw is valuable because pieces connect.

SAGE must therefore treat the **edge/interface between capabilities** as a first-class research object.

Examples:

```text
RECON ──evidence──> CONTEXT
CONTEXT ──belief state──> REASONING
REASONING ──decision candidate──> ASSESSMENT
ASSESSMENT ──uncertainty──> METACOGNITION
METACOGNITION ──risk/bound──> ACTION
ACTION ──effect──> OBSERVATION
OBSERVATION ──outcome──> AUTOPSY
AUTOPSY ──counterfactual──> REGRET
REGRET ──lesson candidate──> LEARNING
LEARNING ──verified update──> MEMORY
MEMORY ──experience──> REASONING
MEMORY ──capability state──> SELF-MODEL
SELF-MODEL ──unknowns──> CURIOSITY
CURIOSITY ──question──> RECON
```

The loop closes without collapsing authority boundaries.

---

## 4. Whole-organism composition

The candidate organism is:

```text
                         ┌───────────────┐
                         │   CURIOSITY   │
                         └───────┬───────┘
                                 │ questions
                                 ▼
┌──────────┐              ┌──────────────┐
│  SENSE   │─────────────>│    CONTEXT   │
└────┬─────┘              └──────┬───────┘
     │                            │
     │ observations               │ state
     ▼                            ▼
┌──────────┐              ┌──────────────┐
│  RECON   │─────────────>│   REASONING  │
└──────────┘              └──────┬───────┘
                                 │ candidates
                                 ▼
                         ┌──────────────┐
                         │ METACOGNITION│
                         └──────┬───────┘
                                │ confidence / uncertainty
                                ▼
                         ┌──────────────┐
                         │   DECISION   │
                         └──────┬───────┘
                                │ authorized action
                                ▼
                         ┌──────────────┐
                         │    ACTION    │
                         └──────┬───────┘
                                │ observed effect
                                ▼
                         ┌──────────────┐
                         │  OBSERVATION │
                         └──────┬───────┘
                                │ outcome
                                ▼
                         ┌──────────────┐
                         │    AUTOPSY   │
                         └──────┬───────┘
                                │ alternatives
                                ▼
                         ┌──────────────┐
                         │COUNTERFACTUAL│
                         └──────┬───────┘
                                │ regret / attribution
                                ▼
                         ┌──────────────┐
                         │   LEARNING   │
                         └──────┬───────┘
                                │ verified candidate
                                ▼
                         ┌──────────────┐
                         │    MEMORY    │
                         └──────┬───────┘
                                │ experience
                                ▼
                         ┌──────────────┐
                         │  SELF-MODEL  │
                         └──────┬───────┘
                                │ capability/unknowns
                                └──────────────> CURIOSITY
```

This is intentionally **not a monolithic “brain module.”** It is a governed network of explicit capability pieces.

---

## 5. Decision quality must be separated from outcome quality

A foundational organism invariant is:

> **An outcome is evidence about what happened. It is not, by itself, proof that the preceding decision was good or bad.**

At minimum:

| Decision quality | Outcome | Interpretation |
|---|---|---|
| Good | Good | successful decision |
| Good | Bad | adverse variance / environment / information shock candidate |
| Bad | Good | false success / lucky result candidate |
| Bad | Bad | genuine decision failure |
| Unknown | Any | insufficient evidence |

The organism should therefore learn from both wins and losses without confusing luck with competence.

---

## 6. Decision Autopsy contract

For consequential decisions, the candidate research contract is:

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

The record must preserve **point-in-time information**. Later knowledge must never leak backward into the historical decision state.

---

## 7. Metacognitive contract

A single confidence score is insufficient.

Candidate dimensions:

1. **Knowledge confidence** — how reliable is the underlying evidence?
2. **Inference confidence** — how strongly does the evidence support the conclusion?
3. **Decision confidence** — how strongly does the conclusion support the selected action?
4. **Outcome attribution confidence** — how confident are we about why the result occurred?
5. **Calibration state** — historically, does expressed confidence track correctness?
6. **Conflict state** — do independent evidence paths disagree?
7. **Unknown state** — what material information is missing?

Metacognition should change behavior. High uncertainty can trigger more recon, narrower claims, lower-risk actions, or a fail-closed STOP when the boundary requires it.

---

## 8. Counterfactual and regret memory

The organism should preserve alternatives rather than only the selected path.

For a decision at time T:

```text
ACTUAL PATH
T0 → A → T1 → B → T2 → OUTCOME

ALTERNATIVE PATHS
T0 → A' → ...
T0 → C  → ...
T0 → D  → ...
```

Counterfactuals are hypotheses unless the alternative is actually observed or supported by a validated model.

**Regret is not punishment.** It is a structured comparison between the chosen action and credible alternatives under the information available at decision time.

This lets SAGE learn:

- from failures;
- from false successes;
- from missed opportunities;
- from unavoidable variance;
- from information that arrived too late;
- from decisions that were correct but poorly executed.

---

## 9. Human experience without human theater

The target is to reproduce useful **functions** of human expertise, not simulate a human personality.

Candidate experience signals include:

- repeated patterns;
- contextual similarity;
- compressed prior cases;
- expert demonstrations;
- expert failures;
- near misses;
- anomalies;
- successful recovery patterns;
- calibrated intuition-like hypotheses.

Do not intentionally add fake hesitation, deliberate mistakes, fake emotion, or arbitrary randomness merely to appear human.

Human-feel should emerge from **context, memory, uncertainty, adaptation, reflection, social understanding, and coherent values**.

---

## 10. Common sense as connected consequence modeling

Common sense should be treated as a research problem in relational consequence, not a magic module.

Candidate capability:

> Given a situation, identify entities, relationships, constraints, likely consequences, missing assumptions, and plausible alternative interpretations before acting.

This should connect:

```text
CONTEXT
  + EXPERIENCE
  + WORLD KNOWLEDGE
  + CONSTRAINTS
  + CAUSAL MODELS
  + UNCERTAINTY
  → CONSEQUENCE MAP
```

The consequence map becomes an input to decision assessment and counterfactual analysis.

---

## 11. Sports / Quantitative Intelligence integration

Issue #365 remains the active Sports/SAGI paper-decision frontier. The Sports subsystem becomes an **organism proving ground**, not a separate intelligence island.

Existing sports recon through Observation 005 contributes concrete data-fabric requirements:

```text
SPORT OBSERVATION
  → MARKET STATE
  → MODEL STATE
  → DECISION STATE
  → TEMPORAL LOCK
  → OUTCOME
  → AUTOPSY
  → COUNTERFACTUAL
  → CALIBRATION
  → REGRET / FAILURE LEARNING
  → OOS VALIDATION
```

Market State candidate schema remains:

`event_id + selection_id + market_type + source/book + observed_at + event_start + raw_odds + normalized_probability + vig_estimate + cross_book_snapshot + movement_path + time_to_event + information_context + close_state + outcome`

The Sports subsystem should therefore test the organism's ability to preserve:

- point-in-time state;
- selection-level identity;
- model/market provenance;
- uncertainty;
- decision quality vs outcome quality;
- variance attribution;
- counterfactuals;
- calibration;
- failure learning;
- OOS integrity.

`wagering_executed = False` remains mandatory.

No real-money authentication, wager placement, payment/wallet automation, bankroll execution, or external wagering is part of this architecture.

---

## 12. Capability Graph becomes the jigsaw board

The existing Capability Graph Engine should be treated as the organism's **jigsaw board**.

It answers:

- What pieces exist?
- What pieces are missing?
- Which pieces depend on each other?
- Which edges are weak or absent?
- Which candidate piece closes the highest-leverage gap?
- What evidence proves the fit?
- What failure would show that the proposed fit is wrong?

This changes capability expansion from:

```text
ADD MODULE
```

to:

```text
IDENTIFY MISSING PIECE
        ↓
IDENTIFY REQUIRED EDGES
        ↓
BUILD PIECE
        ↓
VERIFY INTERFACES
        ↓
ATTACK FAILURE MODES
        ↓
OBSERVE SYSTEM EFFECT
        ↓
PROMOTE ONLY WITH EVIDENCE
```

The graph is therefore not merely an inventory. It becomes a **composition and gap-selection substrate**.

---

## 13. Five-flight Jigsaw execution model

F1–F5 remain **anonymous reusable mission slots**.

The jigsaw architecture does not assign permanent departments to flights.

For every Big Jump Wave:

```text
CAPABILITY GRAPH
      ↓
FIVE DISTINCT MISSING PIECES / EDGES
      ↓
DYNAMIC F1–F5 ASSIGNMENT
      ↓
PARALLEL FULL-STACK EXECUTION
      ↓
SHARED VALIDATED DISCOVERIES
      ↓
C2 RECONVERGENCE
```

A flight may perform research, recon, implementation, repair, verification, integration, or evidence work according to the mission assigned in that wave.

The **mission owns the identity. The flight owns the temporary execution slot.**

---

## 14. Whole-organism shared learning

Validated discoveries should compound across the organism without bypassing governance.

Candidate flow:

```text
LOCAL DISCOVERY
      ↓
EVIDENCE
      ↓
VALIDATION
      ↓
REUSABLE KNOWLEDGE
      ↓
CAPABILITY GRAPH EDGE / PIECE UPDATE
      ↓
OTHER MISSIONS SEE CANDIDATE
      ↓
LOCAL REVALIDATION WHERE REQUIRED
```

A failed experiment also compounds:

```text
FAILURE
 → CLASSIFY
 → PRESERVE
 → EXPLAIN
 → BOUND
 → REGRESSION CASE
 → FUTURE DECISION SIGNAL
```

Negative knowledge is part of the organism's immune memory.

---

## 15. Self-model boundary

SAGE may maintain an evidence-backed **operational self-model** without claiming consciousness.

Candidate self-model fields:

```text
CURRENT_MISSION
ACTIVE_GOALS
KNOWN_CAPABILITIES
DEGRADED_CAPABILITIES
KNOWN_LIMITS
UNKNOWN_MATERIALS
CURRENT_ASSUMPTIONS
CURRENT_CONFIDENCE
RECENT_FAILURES
RECENT_RECOVERIES
CALIBRATION_STATE
AVAILABLE_TOOLS
AUTHORITY_BOUNDARIES
SECURITY_BOUNDARIES
OPEN_QUESTIONS
NEXT_INFORMATION_NEEDS
```

The self-model must be derived from evidence and validated state. It cannot grant itself authority.

---

## 16. Organism-wide governance boundary

The jigsaw does **not** erase separation of authority.

```text
DIRECTOR
  = consequential human authorization

C2
  = intelligence, architecture, governance, verification, advancement judgment

ENGINEERING WORKERS
  = bounded implementation/execution

VALIDATION
  = evidence assessment

MASTER ARCHIVE
  = canonical validated knowledge/state

EXTERNAL RECON
  = intelligence/challenge only
```

A better-connected organism must therefore be **more coherent without becoming less governed**.

---

## 17. Research status and falsification requirements

This architecture is a research candidate until empirical evidence supports specific pieces and edges.

Falsifiable questions include:

1. Does explicit decision-state memory improve post-outcome attribution?
2. Does counterfactual analysis reduce false learning from lucky wins/losses?
3. Does calibrated metacognition improve action selection under uncertainty?
4. Does a self-model improve recovery from capability degradation?
5. Does experience memory improve transfer across related missions?
6. Does curiosity-driven information acquisition improve downstream decision quality enough to justify its cost?
7. Does explicit graph-edge verification reduce integration failures?
8. Does whole-organism shared learning increase verified capability without increasing drift or contamination?
9. Can the same substrate improve multiple domains without creating hidden permanent domain/flight identities?
10. Can Sports serve as a controlled paper-only proving ground for temporal, market, decision, outcome, and learning integrity?

A negative result is a valid result and must remain preserved.

---

## 18. Proposed organism maturity ladder

```text
LEVEL 0 — CAPABILITY PIECES
Modules exist independently.

LEVEL 1 — CONNECTED PIECES
Interfaces and provenance are explicit.

LEVEL 2 — REFLECTIVE ORGANISM
Decision state, autopsy, uncertainty, and failure learning exist.

LEVEL 3 — COUNTERFACTUAL ORGANISM
Alternatives, regret, and variance attribution are measurable.

LEVEL 4 — SELF-MODELING ORGANISM
Capability, limits, calibration, unknowns, and recovery state are evidence-backed.

LEVEL 5 — COMPOUNDING ORGANISM
Validated learning propagates across missions through governed graph edges.

LEVEL 6 — CONTINUOUSLY IMPROVING ORGANISM
The full SENSE → BOUND → ACT → MEASURE → LEARN → VERIFY → IMPROVE loop demonstrates repeatable net capability improvement across domains.
```

These levels are **research milestones**, not automatic qualification states.

---

## 19. Immediate engineering/research frontier

The highest-leverage next step is not to build a fake “consciousness engine.”

It is to make the **jigsaw edges observable and testable**.

Candidate first vertical:

> **Decision Experience Loop v0.1:** connect point-in-time context, belief/uncertainty, action, observed outcome, decision autopsy, counterfactual candidates, variance attribution, regret, and governed learning candidate into one reproducible evidence chain.

Sports/Quantitative Intelligence can provide a bounded paper-only proving ground for this vertical because it already has temporal locking, model/market observations, outcome resolution, calibration, and OOS concepts.

The capability counts only if it produces a real behavior delta such as:

> **Before:** SAGE records what happened but cannot reliably distinguish a bad decision from a bad outcome and cannot preserve credible alternatives at decision time.
>
> **After:** SAGE can reconstruct the decision state, evaluate outcome attribution, preserve counterfactual candidates, generate a bounded learning candidate, and independently verify that the learning did not use future information.

That is a measurable capability jump.

---

## 20. Non-negotiable boundaries

- No consciousness claim from architectural metaphor.
- No fake emotion as an intelligence substitute.
- No deliberate incompetence or arbitrary human-like noise.
- No hindsight leakage into historical decision state.
- No automatic learning promotion from raw outcomes.
- No authority granted by the self-model.
- No permanent F1–F5 identities.
- No strategy promotion from external anecdotes.
- No wagering execution; `wagering_executed = False` remains mandatory.
- No touching PR/issue #349.
- #333 remains parked/locked unless separately authorized.
- Issue #365 remains the active Sports/SAGI frontier unless repo truth establishes a higher-leverage target.
- Git/main and validated Master Archive remain the truth hierarchy.

---

## 21. C2 lock

**JIGSAW WHOLE-ORGANISM PRINCIPLE:**

> **Do not ask which module should become smarter in isolation. Ask which missing piece or missing edge prevents the organism from behaving better as a whole.**

The Capability Graph identifies the missing piece.

The execution slots build it.

The evidence system proves it.

The verification system attacks it.

The Master Archive preserves it.

The organism compounds it.

**Pieces create capability. Connections create the organism. Governance keeps the organism trustworthy.**
