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

- Dimers says its DimersBOT runs at least **10,000 Monte Carlo simulations per event** for NBA, NFL, MLB, and NHL, using rosters, form, previous matchups, weather, and other matchup inputs.
- Dimers says its models calculate probabilities, compare them with sportsbook-implied probabilities, and surface measurable **edge** signals. Its current Best Bets surface is updated as markets move and exposes probability, edge, and best available price across operators.
- Dimers says its models incorporate real-time betting-market movement and update throughout the week as new information arrives.
- Dimers also exposes a distinct **live/in-play probability** product where the model simulates the remainder of a game and updates after every play using current game state and comparable team/player situations.
- Dimers' more advanced Platinum product describes a reinforcement-learning architecture trained on outcomes/profit and loss rather than statistical accuracy alone. This is a vendor claim, not independently validated by C2.
- Dimers also reports independent Pickwatch verification for some historical football-model performance. That claim should be treated as externally asserted evidence requiring direct dataset/methodology inspection before canonical promotion.

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

## Observation 004 — Quantitative bettor history: the real reusable signal is research-system architecture

**Observed source:** Mission Director supplied a search result asking for historically notable sports bettors, including Billy Walters, Bill Benter, Zeljko Ranogajec, Tony Bloom, and Haralabos Voulgaris. C2 then performed independent Super Search across primary/credible reporting, first-party Starlizard material, academic research, and historical technical material.

**Observation date:** 2026-09-01

**Source class:** Historical/academic/commercial recon. **Non-canonical.**

### Raw observations

The names are not being treated as authorities to imitate. The useful signal is the recurring **system architecture** visible across independent accounts:

#### Bill Benter — model + market fusion + continuous re-estimation

Benter's published technical report describes a computerized horse-racing system combining a fundamental handicapping model with public implied probabilities through a logit-based technique. The report describes substantial database/model-development effort, continuing model improvement, and regular re-estimation as new data accumulated. Independent academic history also describes Benter's use of large factor models and market odds as either a comparison target or an input variable.

**Reusable SAGE signal:** the market is not merely an opponent or display; it can be a measurable information source whose relationship to an independent model must itself be learned and evaluated.

#### Tony Bloom / Starlizard — heterogeneous data + weighting + constant iteration + high-performance infrastructure

Starlizard's current first-party description says it consumes information on every aspect of sporting fixtures, analyzes huge volumes of data in real time, produces agile/adaptable models, and continuously iterates them. Historical reporting on Starlizard describes separate research/data and quantitative teams, complex statistical models that weight many inputs, and frequent model updates. The exact proprietary methodology is not public.

**Reusable SAGE signal:** high-quality sports intelligence requires a governed data layer, explicit feature/weight provenance, continuous model iteration, and infrastructure capable of processing event-scale data in real time.

#### Haralabos Voulgaris — deep event-level database + data engineering as capability

Historical interviews describe Voulgaris maintaining a database containing every play from five years of NBA games and spending months engineering the collection/organization so the data became useful for prediction. The important lesson is not his reported betting success; it is that **data acquisition, normalization, and queryable event history were themselves a major capability investment**.

**Reusable SAGE signal:** sports prediction quality is bounded by the quality, granularity, temporal alignment, and engineering of the underlying event data—not merely by model sophistication.

#### Zeljko Ranogajec — economics/operational layer is separate from predictive layer

Historical reporting describes a high-volume quantitative operation built around liquidity, small margins, sophisticated systems, diversification, and negotiated rebates. Rebate economics materially change the economics of a high-volume operation, but they are not a predictive-model capability and are not appropriate to promote into SAGE's paper-only research engine.

**Reusable SAGE signal:** keep **predictive quality**, **market economics**, and **execution economics** as separate analytical layers. Do not let a commercial/rebate mechanism masquerade as model accuracy or predictive edge.

#### Billy Walters — line discrepancy + information/network + market response

Credible historical reporting describes Walters' operation as highly analytical and technically capable, with systematic attention to discrepancies between internal lines and bookmaker lines. Reporting also describes deliberate market-moving activity and distribution/network infrastructure. These execution/manipulation tactics are explicitly excluded from SAGE. The reusable research signal is the distinction between an independent fair-line estimate and an observed market line, plus the need to model how market prices react to information and participation.

**Reusable SAGE signal:** maintain a clean separation between **prediction**, **market observation**, **market response**, and **execution**. SAGE studies the first three; wagering/execution remains disabled.

### Cross-source synthesis

Across these historically different operations, the recurring capability stack is:

> **DATA ACQUISITION → DATA ENGINEERING → FEATURE/FACTOR MODELING → PROBABILITY ESTIMATION → MARKET INFORMATION FUSION → TEMPORAL UPDATES → CALIBRATION / VALIDATION → MARKET-RESPONSE ANALYSIS → OUTCOME LEARNING**

The recurring differentiator is **not one secret betting trick**. It is the construction of a research and decision system that compounds better data, better probability estimates, better market observations, and repeated validation.

### Super Search corroboration

- Benter's technical work explicitly combines fundamental model output with public implied probabilities and describes ongoing re-estimation.
- Starlizard's current first-party material describes real-time data ingestion, large-scale analytics, adaptable models, continuous iteration, and high-performance distributed messaging infrastructure.
- Voulgaris' historical account provides unusually concrete evidence that building and organizing granular event data was itself a major engineering project.
- Academic work reinforces the importance of calibration over raw accuracy for probabilistic sports models, and newer work shows market-price calibration varies with time-to-expiry and product type.
- Research on information release shows that new information can improve line accuracy and reduce line movement as market/oddsmaker forecasts converge; separate research finds information shocks can produce lagged market reactions.
- Current research on in-play forecasting shows that calibrating interpretable models to market prices can materially improve predictive accuracy, reinforcing the value of treating market state as an explicit model input rather than an afterthought.

### New falsifiable research dimensions

1. **Model–market fusion value** — compare independent-model probability, market probability, and fused probability under strict temporal/OOS evaluation.
2. **Factor provenance** — record each feature/factor, source timestamp, transformation, model version, and contribution so model evolution is auditable.
3. **Data-granularity effect** — test whether play/event-level data materially improves calibration versus coarse game-level aggregates.
4. **Continuous re-estimation value** — measure whether scheduled/adaptive model updates improve future calibration without leakage or overreaction to noise.
5. **Market-response decomposition** — separate genuine information shocks from ordinary price noise and market-following behavior.
6. **Market-calibration transfer** — test whether calibrating a sports model to market prices improves OOS performance across leagues/markets or merely transfers market bias.
7. **Non-stationarity / drift** — detect changes by sport, league, market, season phase, and product type; trigger bounded recalibration only when evidence supports it.
8. **Execution-economics isolation** — keep rebates, liquidity, limits, slippage, and execution mechanics analytically separate from predictive edge so research conclusions are not contaminated.
9. **Infrastructure scalability** — test ingestion, normalization, timestamp alignment, lineage, and evaluation at increasing observation volume before claiming capability from model complexity alone.
10. **Independent verification fabric** — preserve external benchmark claims as evidence objects with methodology, cohort, denominator, timestamp, and reproducibility status.

### SAGE gap identified

Observations 002 and 003 identified temporal market state and the Model–Market–Outcome Evaluation Fabric. Observation 004 reveals the deeper missing substrate beneath both:

> **Governed Sports Research Data Fabric**

It should provide canonical paper-only primitives for:

`source observation → normalized event/play state → timestamp → selection identity → feature/factor lineage → model/version → probability → market snapshot → market reference set → calibration → drift state → information shock → close → outcome → OOS evaluation → evidence`

The architecture should support both pregame and live research without collapsing live transitions into static snapshots.

### SAGE action

**Do not copy historical bettor tactics, staking systems, bankroll rules, rebates, market manipulation, or wagering execution.** Extract only the engineering/research primitives that can be tested safely:

- deep historical data;
- event-level normalization;
- factor/feature provenance;
- model-market fusion;
- probability calibration;
- temporal validation;
- continuous but bounded model improvement;
- drift detection;
- market-response analysis;
- independent verification;
- scalable data/lineage infrastructure.

This observation **does not replace the existing frontier**. It identifies the substrate required to make the Temporal Market-State Layer and Model–Market–Outcome Evaluation Fabric genuinely compoundable.

### Boundary

`wagering_executed = False` remains mandatory. No betting, staking, bankroll optimization, rebate exploitation, market manipulation, or wager execution is authorized.

### Evidence status

- Historical architecture signals: **observed**
- Cross-source corroboration: **strong**
- Proprietary tactics/methods: **not treated as canonical**
- Reusable research primitives: **high-value candidate**
- Canonical strategy promotion: **not authorized**
- Next step: **inventory the current SAGE sports-quant data/model/evaluation substrate against this fabric and identify the highest-leverage capability gap before another build wave**
