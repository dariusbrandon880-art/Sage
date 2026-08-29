# SAGE Sports External Signal Addendum

**Status:** Governing research addendum
**Scope:** External/public sports intelligence and observed betting-market behavior
**Boundary:** Research signals only. No sportsbook authentication, account control, deposits, withdrawals, wager placement, or real-money execution.

## 1. Dual-Track Learning Requirement

SAGE MUST maintain two concurrent research tracks for each eligible event cycle:

1. **SAGE Independent Track** — SAGE generates its own probabilities and selections from its governed feature/model pipeline.
2. **External Signal Track** — SAGE observes independently sourced public information, market movement, published odds, publicly visible picks, consensus indicators, analyst selections, and other available pre-event signals.

The external track is an input to learning, not a replacement for SAGE's own prediction.

SAGE MUST be able to answer separately:

- What did SAGE predict?
- What did the external/public sources indicate?
- Where did they agree?
- Where did they diverge?
- Which signal, if any, improved calibrated out-of-sample performance?

## 2. Live External Intelligence

When available through permitted public sources, SAGE may continuously ingest time-stamped pre-event intelligence such as:

- ESPN game/event information and publicly reported availability/news;
- publicly displayed odds and market movement;
- injury, lineup, starter, suspension, and minutes-limit information;
- schedule, travel, rest, weather, venue, and surface context;
- publicly published expert/analyst selections;
- public consensus or pick-distribution indicators;
- other observable pre-event signals from reputable sources.

Each signal MUST carry source, retrieval timestamp, event identifier, signal type, and provenance metadata.

## 3. Public Bet / Pick Behavior as a Research Signal

Where public betting or pick information is lawfully and reliably observable, SAGE may model it as **behavioral market telemetry** rather than ground truth.

Examples include:

- consensus selection percentages;
- public-vs-market divergence indicators;
- published expert picks;
- aggregate pick distributions;
- line movement following observable market information.

SAGE MUST NOT infer that a popular selection is correct merely because it is popular. Crowd behavior is a feature to test, not an oracle.

## 4. Temporal Hygiene

Every external signal is valid only relative to its observation timestamp.

```text
SOURCE EVENT
-> RETRIEVE
-> TIMESTAMP
-> NORMALIZE
-> PROVENANCE HASH
-> AVAILABLE-AT-TIME
-> SAGE MODEL INPUT
-> PRE-EVENT LOCK
```

A signal observed after SAGE's prediction lock MUST NOT modify the locked prediction. It may instead be retained as a diagnostic/post-lock market-response record.

This preserves strict out-of-sample temporal hygiene and prevents hindsight leakage.

## 5. Independent-vs-External Comparison

For every event with sufficient data, the research record SHOULD support:

```text
SAGE PREDICTION
        |
        +----> Outcome Score
        |
        +----> External Signal Comparison
                         |
                         +----> Agreement
                         +----> Divergence
                         +----> Market Response
                         +----> Feature Attribution
```

The system should measure whether external signals improve, degrade, or provide no incremental predictive information relative to SAGE's independent baseline.

## 6. External Signal Learning Gate

External signals MUST pass the same scientific discipline as internal features.

A candidate external signal is promoted only after demonstrating incremental value on locked unseen evaluation data. Useful evaluation axes include:

- Brier score delta;
- log-loss delta;
- calibration reliability;
- resolution;
- CLV/closing-line alignment where valid;
- performance by league, market type, and regime;
- stability across independent evaluation windows.

A signal that improves one historical window but fails OOS validation remains rejected and documented as diagnostic evidence.

## 7. Source Reliability

SAGE SHOULD maintain source-level reliability metadata without treating source reputation as truth.

Reliability dimensions may include:

- timestamp completeness;
- event/entity resolution accuracy;
- update latency;
- historical consistency;
- contradiction rate;
- outcome-independent predictive contribution.

Conflicting sources MUST remain separately attributable until reconciled by evidence.

## 8. Concurrent Operation

The external-intelligence track and SAGE's independent prediction track SHOULD operate concurrently where infrastructure permits.

External observations MUST NOT silently overwrite SAGE-generated probabilities. They enter through an explicit signal boundary so that SAGE can learn whether it benefits from the signal rather than accidentally copying it.

Singles and decomposable parlays remain separate research objects and may be generated concurrently with the two learning tracks.

## Final Lock

```text
SAGE MAKES ITS OWN PICKS.
SAGE ALSO OBSERVES THE PUBLIC/MARKET SIGNAL ENVIRONMENT.

EXTERNAL PICKS = FEATURES, NOT TRUTH.
ESPN/PUBLIC SOURCES = TIME-STAMPED INTELLIGENCE, NOT AUTHORITY.

AGREEMENT + DIVERGENCE = LEARNING DATA.

PRE-LOCK SIGNALS MAY INFORM THE PREDICTION.
POST-LOCK SIGNALS MAY INFORM DIAGNOSTICS, NEVER THE LOCKED RECORD.

NO SOURCE GETS TO REWRITE SAGE'S OWN PREDICTION.

OOS EVIDENCE DECIDES WHETHER AN EXTERNAL SIGNAL EARNS PROMOTION.
```
