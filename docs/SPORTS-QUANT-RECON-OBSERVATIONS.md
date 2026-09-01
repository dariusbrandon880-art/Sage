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

Fresh recon supports the **market-state observation layer**, not the article's promise of a “winning” strategy. Current line-movement tools explicitly timestamp and normalize price changes into implied-probability movement, including FanDuel changes across moneylines, spreads, and totals.

Independent 2026 research describes odds as information-bearing market signals and notes that bettors use line movement to infer updated information, while also warning that implied probabilities can be misleading because of randomness or market mispricing.

A current FanDuel market-data feed advertises pre-match/live coverage, player props, alternates, and real-time normalized odds, reinforcing that timestamped market snapshots are a practical data primitive for research.

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

The existing sports ingestion boundary already preserves `event_id`, sport/league, event start, observation timestamp, market, prices, source, source URL, and metadata, which is sufficient groundwork for time-indexed research.

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

## Observation 003 — Dimers: production sports-analytics architecture signal

**Observed source:** Dimers/Wikipedia description supplied to C2 by Mission Director, followed by current Dimers Super Search reconnaissance.

**Observation date:** 2026-09-01

**Source class:** External commercial/product recon plus secondary reference. **Non-canonical.**

### Raw observations

The supplied source identifies Dimers as a sports analytics platform under Cipher Sports Technology Group, combining predictive analytics, machine learning, odds comparison, news/content, and B2B analytics. Current first-party reconnaissance adds several concrete architecture signals:

- Dimers says its DimersBOT runs at least **10,000 Monte Carlo simulations per event** for NBA, NFL, MLB, and NHL, using rosters, form, previous matchups, weather, and other matchup inputs. citeturn0search0turn0search9
- Dimers says its models calculate probabilities, compare them with sportsbook-implied probabilities, and surface measurable **edge** signals. Its current Best Bets surface is updated as markets move and exposes probability, edge, and best available price across operators. citeturn0search8turn0search4
- Dimers says its models incorporate real-time betting-market movement and update throughout the week as new information arrives. citeturn0search4
- Dimers also exposes a distinct **live/in-play probability** product where the model simulates the remainder of a game and updates after every play using current game state and comparable team/player situations. citeturn0search11
- Dimers' more advanced Platinum product describes a reinforcement-learning architecture trained on outcomes/profit and loss rather than statistical accuracy alone. This is a vendor claim, not independently validated by C2. citeturn0search5turn0search10
- Dimers also reports independent Pickwatch verification for some historical football-model performance. That claim should be treated as externally asserted evidence requiring direct dataset/methodology inspection before canonical promotion. citeturn0search2

### C2 interpretation

The strongest reusable signal is **architectural decomposition**, not “copy Dimers betting strategy.” Dimers publicly describes a production loop that separates several research primitives SAGE is already beginning to model:

> **DATA → SIMULATION / PROBABILITY → MARKET COMPARISON → EDGE SIGNAL → CONTINUOUS UPDATE → LIVE STATE → OUTCOME EVALUATION**

This matters because it exposes a concrete capability frontier for SAGE: a sports quantitative system should not be only a static odds calculator or a single prediction function. It should preserve the lineage between **raw observation, model probability, market probability, temporal state, information updates, and eventual outcome** so each signal can be evaluated independently and OOS.

### New falsifiable research dimensions

1. **Simulation-to-probability calibration** — test whether simulation-derived probabilities remain calibrated OOS across sport, market, horizon, and sample size.
2. **Probability-to-market edge decomposition** — separate model probability, market-implied probability, de-vig adjustment, and the resulting delta/edge into auditable fields.
3. **Continuous-update value** — measure whether incorporating timestamped market movement and new information improves calibration or only tracks the market.
4. **Live-state transition modeling** — represent live observations as sequential state transitions with event/play timestamps rather than treating them as independent snapshots.
5. **Model-vs-market attribution** — determine whether apparent edge comes from model signal, stale market data, information latency, or random variance.
6. **Outcome-trained learning claims** — investigate whether outcome/profit-trained models outperform accuracy-trained baselines under controlled OOS evaluation without allowing wagering execution.
7. **Independent verification lineage** — preserve third-party verification source, methodology, cohort, timestamp, and denominator so external performance claims can be reproduced or falsified.
8. **Coverage-scale data architecture** — investigate the engineering requirements for high-volume probability/line/edge records without conflating volume with predictive quality.

### SAGE gap identified

Observation 002 identified the **Temporal Market-State Research Layer**. Dimers makes the next missing boundary clearer: SAGE needs a governed **Model–Market–Outcome Evaluation Fabric** that can join, at exact timestamps and exact selection identity:

`observation → model version → model probability → market snapshot(s) → implied/de-vig probability → edge decomposition → information state → close → resolved outcome → OOS evaluation`

For live products, the chain must additionally preserve:

`event state T0 → state transition T1 → ... → state Tn → final outcome`

This is a real capability frontier because it enables SAGE to answer not merely “what probability did the model output?” but **why did the model differ from the market, what information was available then, how did the market respond, and did the signal survive independent out-of-sample evaluation?**

### SAGE action

**Do not copy Dimers' proprietary claims or promote its “winning,” ROI, or +EV language into SAGE strategy.** Promote the measurable architecture primitives only:

- simulation provenance;
- model/version identity;
- probability snapshots;
- market snapshots and best-price references;
- de-vig/implied-probability normalization;
- edge decomposition;
- temporal and live-state lineage;
- information-shock provenance;
- outcome resolution;
- independent/OOS verification.

This observation therefore **extends Observation 002 rather than replacing it**. The temporal market-state layer remains the immediate substrate; the broader frontier is now a governed **Model–Market–Outcome Evaluation Fabric**.

### Boundary

`wagering_executed = False` remains mandatory. Dimers is being used as external recon about production sports-analytics architecture, not as authorization to bet, stake, optimize bankrolls, or execute wagers.

### Evidence status

- External observation: **observed**
- First-party product architecture signals: **corroborated by current Dimers pages**
- Vendor performance claims: **unvalidated by SAGE**
- Reusable architecture primitives: **high-value candidate**
- Canonical strategy promotion: **not authorized**
- Next step: **design/implement a paper-only Model–Market–Outcome Evaluation Fabric against exact selection identity and timestamped observations, then validate OOS**
