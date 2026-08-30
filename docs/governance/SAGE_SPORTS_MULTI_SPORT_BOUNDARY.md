# SAGE Sports Multi-Sport Boundary

## Authority

This document defines the sport-domain boundary for SAGE C2. It does not replace the validated Sports/RCE substrate governed by the existing Sports/RCE contract lineage.

## Canonical rule

SAGE does not create independent MLB, NBA, NFL, NHL, soccer, or tennis prediction engines. Sports-specific behavior is bounded to adapters for event/competition normalization and feature/outcome translation. Forecast locking, provenance, temporal integrity, immutable receipts, scoring, calibration, and C2 promotion remain canonical concerns.

## Canonical forecast envelope

Every sports forecast must be representable by:

- event identity;
- sport and competition identity;
- scheduled start time;
- observation cutoff;
- forecast lock;
- point-in-time feature availability/provenance;
- source identifiers and hashes;
- forecast and model version;
- immutable forecast receipt;
- independently sourced outcome resolution;
- walk-forward out-of-sample scoring;
- calibration/drift state;
- C2 promotion decision.

## Competition frontier

The architecture is extensible across baseball, basketball, football, hockey, soccer, tennis, and future sports. Initial competition adapters may include MLB, NBA, WNBA, NCAAB, NFL, NCAAF, NHL, ATP, WTA, plus extensible soccer competitions. Listing a competition is a capability boundary, not evidence that live ingestion is currently operational.

## Temporal safety

A feature may be used only if it was available at or before the observation cutoff. The forecast lock must precede the scheduled event start. Outcome data is strictly post-event and cannot influence the locked forecast. Ambiguous or missing timestamps fail closed.

## Synthetic-data boundary

Synthetic fixtures are permitted only in explicitly isolated tests. Production or shadow execution must never substitute fabricated events, odds, provider observations, timestamps, or outcomes for missing external data. Missing or invalid provider data is represented as unavailable/fail-closed.

## Evidence boundary

Implementation success, local test success, runtime execution, empirical outcome evidence, and customer/operator acceptance are separate states. A unit test or generated receipt cannot by itself establish real-world acceptance or promotion eligibility.

## Reconciliation rule

Reuse the existing Sports/RCE primitives before introducing new ones. Any new multi-sport abstraction must either wrap an existing canonical primitive or demonstrate a concrete correctness gap that the existing substrate cannot satisfy. Duplicate ledgers, prediction engines, schedulers, or evidence systems are prohibited without a separately authorized architecture decision.
