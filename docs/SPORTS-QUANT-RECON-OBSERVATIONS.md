# SAGE Sports Quant — Recon Observation Log

## Observation 001 — FanDuel / Reddit parlay strategy claim

**Observed source:** Reddit sports-betting discussion supplied to C2 by Mission Director.

**Observation date:** 2026-09-01

**Source class:** External social recon. **Non-canonical.**

### Raw claims observed

The supplied discussion contains community claims including:

- Large parlays frequently fail on one or more legs.
- Some users advocate choosing lower/higher-priced legs and changing wager size; the original author explicitly corrected “lowest odds” to “highest odds.”
- Matchup research, injury reports, usage/context, and player statistics are repeatedly cited as useful inputs.
- Several commenters favor shorter 2–4 leg combinations over very large parlays.
- Same Game Parlay (SGP) users discuss correlated legs and adjusted prices.
- Users report personal records or profitability without providing controlled, complete samples sufficient to establish causal or predictive validity.

### C2 interpretation

These statements are **hypotheses/signals, not betting rules**. SAGE must not promote them into canonical strategy merely because they recur in social discussion.

Candidate research dimensions:

1. **Leg-count effect** — measure how joint hit probability, calibration, expected value, and realized paper performance change as leg count increases.
2. **Price/odds selection effect** — normalize American odds to probabilities/decimal prices and test whether price bands contain measurable incremental predictive information after controlling for market probability.
3. **Context-feature value** — test matchup, injury, usage, role, game-script, and sport-specific context as explanatory variables rather than assuming they create edge.
4. **Player reputation vs prop value** — explicitly separate player quality from market mispricing.
5. **SGP dependence** — estimate empirical joint probabilities/correlation instead of multiplying marginal probabilities when legs are not independent.
6. **Boost/markup effect** — compare quoted parlay/SGP prices against the joint probability implied by component markets and historical outcomes.
7. **Self-reported profitability quality** — distinguish anecdotal claims from reproducible, timestamped, selection-level paper records.

### Super Search corroboration

External recon found multiple independent discussions warning that long parlays frequently miss by one leg, while other communities advocate shorter combinations. These are sentiment signals only. A separate 2026 research paper reports systematic overpricing of cross-game parlays relative to the product of contemporaneous leg prices, with overpricing increasing with leg count, and emphasizes conditioning probability calibration on time-to-expiry and product type. citeturn0reddit22turn0reddit30turn0academia23

Additional recon confirms that SGP pricing can explicitly adjust for perceived correlation and may include additional bookmaker margin beyond simple leg multiplication. citeturn0reddit35

### SAGE action

**Do not encode the Reddit claims as rules.** Convert them into paper-only experiments against timestamped selection-level observations.

Priority capability frontier:

> **Selection-level parlay/SGP research engine:** ingest observed market snapshots, preserve temporal locks, estimate marginal and joint probabilities, quantify correlation and pricing/boost effects, evaluate calibration and realized paper outcomes by exact selection identity, and retain falsified/validated hypotheses.

### Boundary

`wagering_executed = False` remains mandatory. This report records external observations and research hypotheses; it does not authorize or execute wagering.

### Evidence status

- External observation: **observed**
- Cross-source recon: **corroborated as a research topic**
- Strategy validity: **unvalidated**
- Canonical promotion: **not authorized**
- Next step: **collect controlled paper observations and test the hypotheses**
