# SAGE Sports Multi-Sport Boundary

## Mission

SAGE sports forecasting is a sport-agnostic shadow/research domain. MLB is one adapter, not the architecture.

## Canonical contract

Every supported competition must pass the same immutable boundary:

1. event identity;
2. competition/league identity;
3. scheduled start time;
4. observation cutoff;
5. forecast lock;
6. feature-level point-in-time provenance;
7. source hashes;
8. model forecast;
9. immutable forecast receipt;
10. independently sourced outcome resolution;
11. walk-forward scoring/calibration;
12. C2 promotion gate.

## Adapter rule

External sport and competition payloads are normalized through bounded adapters. Adapters may translate identifiers, schedules, competitors, markets, and provider-specific fields. They must not become separate prediction engines.

Current declared competition registry:

- Baseball: MLB
- Basketball: NBA, WNBA, NCAAB
- Football: NFL, NCAAF
- Hockey: NHL
- Tennis: ATP, WTA
- Soccer/Football: extensible domestic, international, and tournament competitions

The registry is a capability boundary, not a claim that live data ingestion is currently active for every competition.

## Synthetic-data prohibition

Production/shadow forecasting paths must not manufacture events, odds, consensus, results, timestamps, or provider observations when external data is unavailable. Test fixtures may be synthetic only when explicitly isolated as tests and never promoted as real-world evidence.

A missing provider is represented as unavailable/fail-closed, not substituted with fabricated observations.

## Evidence rule

A successful adapter normalization does not establish a forecast. A forecast does not establish an outcome. An outcome does not establish promotion eligibility. Each stage requires its own timestamped, hashed evidence and remains subject to the C2 promotion gate.
