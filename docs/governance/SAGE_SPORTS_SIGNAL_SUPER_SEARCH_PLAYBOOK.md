# SAGE Sports Signal Super Search Playbook

## Operating Rule

Super Search is a sensor inside the SAGE build loop, never an authority and never a hindsight oracle.

## Search Before Target Selection

For each Big Jump Wave, F1 identifies the highest-leverage unresolved signal frontier using current repository truth first. External search may then sharpen the hypothesis with current information about:

- injuries, scratches, suspensions, and confirmed lineups;
- player/team role and availability changes;
- schedules, rest, travel, and environmental conditions;
- market movement and data-quality limitations;
- quantitative forecasting and calibration methodology;
- documented failure modes in sports prediction systems.

## Evidence Boundary

Every imported observation must retain source identity, observation timestamp, retrieval timestamp, event identity, and the exact normalized claim. A later retrieval must not be treated as evidence that was available at an earlier prediction lock.

## Falsification

Search findings are candidate signals until tested against locked historical or live-shadow OOS events. SAGE must actively look for evidence that a proposed signal is stale, noisy, duplicated by the market baseline, or only apparently predictive because of leakage.

## No Hindsight Contamination

Post-event articles, final injury reports, final scores, and retrospective explanations may be used for diagnostics only. They cannot modify a prediction that was already locked or enter the generation feature set for that event.

## Five-Flight Integration

F1 discovers and normalizes signals. F2 preserves provenance and lineage. F3 consumes only eligible signals during concurrent generation. F4 enforces temporal and leakage gates. F5 attributes signal contribution and turns validated patterns into candidate strategy hypotheses.

## Velocity

Search work counts toward verified velocity only when it produces a reusable, tested capability or materially improves a validated prediction signal. Search-result volume, number of articles, or number of generated picks is not capability velocity by itself.
