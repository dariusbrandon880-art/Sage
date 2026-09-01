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

> **DATA ACQUISITION → DATA ENGINEERING → FEATURE/FACTOR MODELING → PROBABILITY ESTIMATION → MARKET FUSION → TEMPORAL UPDATE → CALIBRATION → DRIFT/ERROR → OUTCOME LEARNING**

This is a stronger architectural signal than any individual bettor's “strategy.”

### SAGE gap identified

The next missing layer is a governed **Sports Research Data Fabric** capable of preserving raw observations, normalized event/play state, timestamp alignment, feature/factor lineage, model/version lineage, probability snapshots, market snapshots, calibration, drift/error, information shocks, outcomes, and OOS evidence.

### SAGE action

Historical bettors are treated as **architecture-recon subjects**, not strategy authorities. Their proprietary tactics, execution methods, market manipulation, bankroll/rebate optimization, and wagering instructions are not promoted into SAGE.

### Boundary

`wagering_executed = False` remains mandatory.

### Evidence status

- Historical architecture signals: **observed**
- Cross-source recurrence: **strong**
- Proprietary methods: **unknown/unvalidated**
- Reusable architecture primitives: **high-value candidate**
- Canonical strategy promotion: **not authorized**
- Next step: **design the Sports Research Data Fabric and validate its temporal/model/market/outcome lineage**

## Observation 005 — Odds literacy + line-movement education: turn the visible market board into measurable state

**Observed sources:** Mission Director supplied four educational/search surfaces: 2eZ Sports Betting “How to Read Sports Odds & Line Movement,” Caan Berry Pro Trader “How Betting Odds Work in 8 Minutes,” Hard Rock Bet “How To Understand Odds,” FanDuel “Understanding How Odds Work at FanDuel Sportsbook,” plus Sportsbook Review and Oddschecker odds/line-movement surfaces.

**Observation date:** 2026-09-01

**Source class:** Educational/commercial external recon. **Non-canonical.**

### What the supplied material actually adds

The 2eZ video explicitly teaches reading odds charts, line movement, sharp-vs-public shifts, and real-time market changes. Search metadata confirms those are the video's stated topics, but C2 did **not** claim to have watched the full 24:49 video from metadata alone. citeturn1youtube26

FanDuel's official odds explainer establishes the underlying display semantics: negative odds represent the amount needed to win $100, positive odds represent the profit on a $100 stake, and the sign conveys an implied-likelihood relationship rather than a guarantee. citeturn0search0turn0youtube54

Oddschecker currently exposes real-time cross-book moneyline, spread, and total prices and explicitly compares independent sportsbook prices side-by-side. Its NFL pages also describe line movement from opening through closing and distinguish market movement associated with injuries/weather/financial action. These commercial explanations are hypotheses about causes, not proof that a particular movement is “sharp money.” citeturn1search0turn1search1

### Super Search — deeper research signal

The research layer is materially stronger than beginner education alone:

1. **Odds are not probabilities by default.** A quoted price contains margin and may exhibit calibration bias. A 2026 study using 90,014 football matches across five bookmakers proposes an odds-only conversion method because existing conversion methods can misrepresent bookmaker pricing objectives and biases. citeturn0academia58
2. **Calibration is temporal.** A 2026 study using 23 million sports event-contract trades found calibration changes with time-to-expiry and becomes sharply distorted near settlement. It also found systematic cross-game parlay overpricing increasing with leg count. citeturn0academia56
3. **Line movement is measurable rather than mystical.** A newly published open dataset contains 11.7 million odds snapshots from 52 bookmakers across 13+ sports and explicitly measures open-to-close de-vig probability movement and distance-to-close by time-to-start. citeturn0search8turn0search14
4. **Movement can show serial structure.** A 2025 study of NFL/NBA/NHL moneyline movement from opening to closing found significant negative autocorrelation across all three sports, consistent with broad overreaction characteristics. This is evidence for a research hypothesis, not a universal exploitable rule. citeturn0search5
5. **Information shocks have measurable lag/response structure.** A 2025 Economic Inquiry study analyzed 117,174 odds from 32 bookmakers around elite-player absence announcements and found initial inertia followed by lagged price reaction. citeturn0search2
6. **High-frequency state matters.** Research using second-by-second in-play football prices and volumes demonstrates why price *and quantity* should be joined when studying market reaction to breaking events. citeturn0search11
7. **Markets do not necessarily anticipate major events.** A 1-Hz Bundesliga study found neither bookmakers nor bettors significantly anticipated first goals immediately before they occurred. This is a useful negative result against naive “the market knows before the event” assumptions. citeturn0academia57
8. **Market calibration can itself be a model feature.** A 2026 in-play football paper found calibrating model parameters to pre-match exchange prices was the dominant driver of predictive accuracy in its tested models. This is highly relevant to SAGE as a model-market fusion hypothesis, but its betting simulation result is not a target capability for SAGE. citeturn0academia55
9. **Anchoring is another measurable market-state variable.** A 2025 NFL study found preseason Super Bowl odds continued to influence bettor behavior and sportsbook closing lines weeks into the season. citeturn0search1turn0search3

### C2 interpretation

The beginner videos are therefore useful primarily as **schema reconnaissance**: they reveal the vocabulary and visual state that a human market observer sees — odds format, price direction, line movement, public/sharp labels, opening/closing state, and live updates.

SAGE should translate that visible vocabulary into **machine-auditable state**, not into betting advice.

The new canonical research primitive candidate is:

> **Market State = timestamped price + normalized probability + margin/vig estimate + market/selection identity + source/book + cross-book state + time-to-event + movement trajectory + information context + eventual close/outcome.**

### New falsifiable research dimensions

1. **Odds-format normalization** — American, decimal, fractional, and probability representations must round-trip without semantic loss.
2. **Vig/de-vig model comparison** — compare multiple probability-normalization methods by sport, market type, bookmaker, and time-to-event; do not assume one universal conversion is correct.
3. **Open-to-close trajectory** — model the complete path, not only opening and closing values.
4. **Distance-to-close curve** — quantify how informative an observation at T is about the eventual close, segmented by sport/market/time horizon.
5. **Cross-book dispersion** — preserve the full contemporaneous distribution rather than only the “best price.”
6. **Movement attribution** — distinguish observed movement from inferred cause; attach information shocks where evidence exists instead of labeling every move “sharp money.”
7. **Autocorrelation/overreaction** — test whether movement persistence/mean reversion is stable across sport, market, season, and regime.
8. **Anchoring** — test whether stale prior expectations continue influencing later market prices after controlling for current information.
9. **Quantity + price fusion** — where available, join transaction volume/count with price movement to separate participation effects from pure price relocation.
10. **Live state transitions** — preserve event-by-event/second-by-second state where available rather than reducing live markets to isolated snapshots.
11. **Negative-signal preservation** — explicitly retain cases where apparent movement signals fail, including the Bundesliga pre-goal anticipation result.
12. **Market-calibrated model fusion** — compare model performance with and without market-state calibration to determine whether the market contributes independent predictive information or merely tracks it.

### SAGE gap identified

Observation 004 proposed the **Sports Research Data Fabric**. Observation 005 makes its minimum market-state schema more concrete:

`event_id + selection_id + market_type + source/book + observed_at + event_start + raw_odds + normalized_probability + vig_estimate + cross_book_snapshot + movement_path + time_to_event + information_context + close_state + outcome`

That schema should be immutable at observation time and append-only across updates. Derived values must retain method/version lineage so SAGE can reproduce why a probability or edge was calculated.

### SAGE action

**Do not promote “sharp money,” “reverse line movement,” “best odds,” or “CLV = guaranteed predictive skill” as rules.** They are research labels/hypotheses requiring empirical validation.

Promote the underlying **market-observation primitives** into the Sports Research Data Fabric and Model–Market–Outcome Evaluation Fabric.

The next engineering target is therefore not an odds tutorial or betting recommendation engine. It is a **reproducible Market-State Capture + Normalization + Trajectory layer** that feeds paper-only evaluation.

### Boundary

`wagering_executed = False` remains mandatory. No wagering, staking, bankroll optimization, or execution is authorized by this observation.

### Evidence status

- Educational market vocabulary: **observed**
- Odds/line semantics: **corroborated**
- Temporal calibration effects: **strong external research signal**
- Open line-movement dataset: **available external research signal**
- “Sharp money” causal interpretation: **unvalidated**
- Market-state schema: **high-value architecture candidate**
- Canonical strategy promotion: **not authorized**
- Next step: **implement paper-only market-state capture/normalization/trajectory primitives and validate against exact timestamped observations**
