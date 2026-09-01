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

External recon found multiple independent discussions warning that long parlays frequently miss by one leg, while other communities advocate shorter combinations. These are sentiment signals only. A separate 2026 research paper reports systematic overpricing of cross-game parlays relative to the product of contemporaneous leg prices, with overpricing increasing with leg count, and emphasizes conditioning probability calibration on time-to-expiry and product type.

Additional recon confirms that SGP pricing can explicitly adjust for perceived correlation and may include additional bookmaker margin beyond simple leg multiplication.

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

## Observation 002 — SportyTrader FanDuel strategy article: probability, timing, and live-state signals

**Observed source:** SportyTrader “How to Win a Bet on FanDuel Sportsbook,” supplied to C2 by Mission Director.

**Observation date:** 2026-09-01

**Source class:** Commercial/editorial external recon. **Non-canonical.**

### Raw claims observed

The article presents several recurring strategy claims:

- Convert sportsbook odds into implied probabilities and compare those probabilities with an independent estimated probability.
- Treat a market as potentially valuable when an independently estimated probability materially exceeds the market-implied probability.
- Monitor odds movement rather than treating the displayed price as static.
- Consider earlier market prices when a bettor expects the market to move.
- Player-availability uncertainty can be reflected in prices and can change as information arrives.
- Live betting should be informed by pre-game research plus current game state and sport knowledge.

### Super Search corroboration

Fresh recon supports the **market-state observation layer**, not the article's promise of a “winning” strategy. Current line-movement tools explicitly timestamp and normalize price changes into implied-probability movement, including FanDuel changes across moneylines, spreads, and totals. citeturn0search0turn0search3

Independent 2026 research describes odds as information-bearing market signals and notes that bettors use line movement to infer updated information, while also warning that implied probabilities can be misleading because of randomness or market mispricing. citeturn0search18

A current FanDuel market-data feed advertises pre-match/live coverage, player props, alternates, and real-time normalized odds, reinforcing that timestamped market snapshots are a practical data primitive for research. citeturn0search4

### C2 interpretation

The strongest signal here is **not “bet early” or “live bet.”** The reusable SAGE signal is:

> **Market price is a time-indexed observation whose informational value must be evaluated relative to timestamp, market state, competing prices, and eventual close/outcome.**

That produces several falsifiable research dimensions:

1. **Implied-probability delta** — compare model probability vs de-vigged market probability at observation time.
2. **Time-to-event effect** — measure whether predictive/calibration quality changes as event start approaches.
3. **Line-movement signal** — test whether direction/magnitude of movement predicts closing price or outcome after controlling for opening price and market type.
4. **Cross-book consensus** — compare FanDuel price against contemporaneous multi-book consensus and sharp-reference prices rather than treating one retail book as ground truth.
5. **Early-vs-late observation value** — measure whether an earlier timestamp contains useful information about later closing prices, without converting that finding into wagering instructions.
6. **Live-state research** — model live observations as a distinct product type with state transitions, not as ordinary pregame snapshots.
7. **Information-shock attribution** — preserve injury/news/status changes as timestamped context so line movement is not falsely interpreted as predictive skill.

### SAGE gap identified

The existing sports ingestion boundary already preserves `event_id`, sport/league, event start, observation timestamp, market, prices, source, source URL, and metadata, which is sufficient groundwork for time-indexed research. fileciteturn149file0

The next capability gap is **not another odds calculator**. It is a controlled temporal market-observation/evaluation layer that can answer:

- What was known at timestamp T?
- What was the price at T across available references?
- How did that price move afterward?
- Did the movement predict the close, the outcome, neither, or merely reflect an information shock?
- Does the signal remain calibrated out-of-sample?

### SAGE action

**Do not encode SportyTrader's “how to win” claims as rules.** Promote only the underlying measurable primitives into research infrastructure: timestamped prices, implied probabilities, cross-book comparison, line movement, time-to-event, live/pre-game product distinction, and information-shock provenance.

This observation strengthens the existing **Selection-level parlay/SGP research engine** frontier and adds a temporal market-state dimension to it.

### Boundary

`wagering_executed = False` remains mandatory. No betting, staking, bankroll optimization, or wager execution is authorized by this observation log.

### Evidence status

- External observation: **observed**
- Cross-source market-state corroboration: **corroborated**
- Specific strategy validity: **unvalidated**
- Temporal research value: **high candidate**
- Canonical promotion: **not authorized**
- Next step: **collect timestamped paper observations and evaluate movement/close relationships out-of-sample**
