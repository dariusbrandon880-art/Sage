"""Concurrent paper-prediction generation with immutable pre-event locks."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Iterable, Mapping, Sequence, Any

from .ingestion import MarketSnapshot, PlayerPropSnapshot, FanDuelSnapshotAdapter
from .evaluation import calculate_ev, calculate_kelly_stake


@dataclass(frozen=True)
class PropEdgeResult:
    player_name: str
    prop_category: str
    selection: str
    fanduel_decimal_price: float
    fanduel_implied_prob: float
    projected_prob: float
    edge_score: float
    expected_value: float
    confidence_score: float
    is_positive_ev: bool
    kelly_stake_recommendation: float
    rationale: str


def evaluate_sgp_boost(
    legs: Sequence[PropEdgeResult], boosted_decimal_price: float
) -> dict[str, Any]:
    """Evaluate FanDuel Same Game Parlay (SGP) Plus boost quality and correlation."""
    if not legs:
        raise ValueError("SGP_REQUIRES_LEGS: at least one leg is required")
    if boosted_decimal_price <= 1.0:
        raise ValueError("INVALID_BOOSTED_PRICE: boosted decimal price must be > 1.0")

    all_individual_positive = all(leg.is_positive_ev for leg in legs)
    fair_prob_product = 1.0
    fd_implied_product = 1.0
    for leg in legs:
        fair_prob_product *= leg.projected_prob
        fd_implied_product *= leg.fanduel_implied_prob

    boosted_ev = (fair_prob_product * boosted_decimal_price) - 1.0
    all_overs = all("over" in leg.selection.lower() or "yes" in leg.selection.lower() for leg in legs)

    if all_individual_positive and boosted_ev > 0:
        recommendation = "GRAVY"
        assessment = "Positive individual leg EV combined with boost enhancement."
    elif boosted_ev > 0 and not all_overs:
        recommendation = "GENUINE_PLUS_EV"
        assessment = "Boost overcomes un-correlated or negatively correlated leg combination."
    elif all_overs and boosted_ev <= 0.05:
        recommendation = "BOOST_TRAP"
        assessment = "Positively correlated all-over SGP where boost fails to compensate joint risk."
    elif boosted_ev <= 0:
        recommendation = "BOOST_TRAP"
        assessment = "Negative EV parlay despite boosted pricing."
    else:
        recommendation = "CONDITIONAL_ACCEPT"
        assessment = "Moderate boost value subject to strict bankroll controls."

    return {
        "leg_count": len(legs),
        "all_legs_positive_ev": all_individual_positive,
        "joint_fair_probability": round(fair_prob_product, 6),
        "joint_fd_implied_probability": round(fd_implied_product, 6),
        "boosted_decimal_price": boosted_decimal_price,
        "boosted_expected_value": round(boosted_ev, 4),
        "recommendation": recommendation,
        "assessment": assessment,
    }


class FanDuelPlayerPropAnalyzer:
    """Quantitative research engine for FanDuel Player Props (+EV, Edge, and Confidence analysis)."""

    def __init__(self, model_version: str = "propsbot-ai-v1") -> None:
        self.model_version = model_version

    def analyze_prop(
        self,
        snapshot: PlayerPropSnapshot,
        selection: str = "over",
        red_zone_touch_share: float | None = None,
        game_script_bias: float | None = None,
        usage_rate: float | None = None,
        shot_volume_expectation: float | None = None,
    ) -> PropEdgeResult:
        if selection not in snapshot.prices:
            if selection == "over" and "yes" in snapshot.prices:
                selection = "yes"
            elif selection == "under" and "no" in snapshot.prices:
                selection = "no"
            elif selection not in snapshot.prices:
                selection = next(iter(snapshot.prices))

        fd_price = snapshot.prices[selection]
        fd_implied = FanDuelSnapshotAdapter.implied_probability(fd_price)

        if snapshot.sharp_reference_price and snapshot.sharp_reference_price > 1.0:
            sharp_implied = FanDuelSnapshotAdapter.implied_probability(snapshot.sharp_reference_price)
            base_prob = sharp_implied
            confidence_base = 0.85
        else:
            base_prob = fd_implied
            confidence_base = 0.65

        adjustment = 0.0
        rationales = []
        category = snapshot.prop_category.lower()

        if "touchdown" in category or category == "atd":
            if red_zone_touch_share is not None:
                rz_delta = (red_zone_touch_share - 0.20) * 0.25
                adjustment += rz_delta
                rationales.append(f"Red-zone touch share {red_zone_touch_share:.0%}")
            if game_script_bias is not None:
                adjustment += game_script_bias * 0.05
                rationales.append(f"Game script bias {game_script_bias:+.2f}")
        elif "points" in category or "rebounds" in category or "double" in category or "three" in category or "pra" in category:
            if usage_rate is not None:
                usage_delta = (usage_rate - 0.22) * 0.30
                adjustment += usage_delta
                rationales.append(f"Usage rate {usage_rate:.0%}")
        elif "shots" in category or "sog" in category or "saves" in category:
            if shot_volume_expectation is not None:
                vol_delta = (shot_volume_expectation - 2.5) * 0.04
                adjustment += vol_delta
                rationales.append(f"Shot volume expectancy {shot_volume_expectation:.1f}")

        projected_prob = min(0.95, max(0.05, base_prob + adjustment))
        edge_score = projected_prob - fd_implied
        ev = calculate_ev(projected_prob, fd_price)
        kelly = calculate_kelly_stake(projected_prob, fd_price, wagering_executed=False)
        confidence = min(1.0, max(0.1, confidence_base + abs(adjustment) * 0.5))

        rationale_text = f"Prop {snapshot.player_name} ({snapshot.prop_category}): FD implied {fd_implied:.1%}, model projected {projected_prob:.1%}."
        if rationales:
            rationale_text += " " + "; ".join(rationales)

        return PropEdgeResult(
            player_name=snapshot.player_name,
            prop_category=snapshot.prop_category,
            selection=selection,
            fanduel_decimal_price=fd_price,
            fanduel_implied_prob=round(fd_implied, 4),
            projected_prob=round(projected_prob, 4),
            edge_score=round(edge_score, 4),
            expected_value=round(ev, 4),
            confidence_score=round(confidence, 4),
            is_positive_ev=ev > 0,
            kelly_stake_recommendation=round(kelly, 4),
            rationale=rationale_text,
        )

    def generate_prop_prediction(
        self,
        snapshot: PlayerPropSnapshot,
        edge_result: PropEdgeResult,
        cycle_id: str,
    ) -> "PredictionRecord":
        safe_player = snapshot.player_name.replace(" ", "_")
        record = PredictionRecord(
            prediction_id=f"pred_prop_{cycle_id}_{snapshot.event_id}_{safe_player}_{edge_result.selection}",
            cycle_id=cycle_id,
            event_id=snapshot.event_id,
            market=snapshot.prop_category,
            selection=f"{snapshot.player_name} - {edge_result.selection}",
            model_version=self.model_version,
            predicted_probability=edge_result.projected_prob,
            market_probability=edge_result.fanduel_implied_prob,
            observed_at_utc=snapshot.observed_at_utc,
            event_start_utc=snapshot.event_start_utc,
        )
        return record.sign()


@dataclass(frozen=True)
class PredictionRecord:
    prediction_id: str
    cycle_id: str
    event_id: str
    market: str
    selection: str
    model_version: str
    predicted_probability: float
    market_probability: float
    observed_at_utc: str
    event_start_utc: str
    is_oos: bool = True
    is_parlay: bool = False
    parent_prediction_id: str | None = None
    legs: tuple[str, ...] = field(default_factory=tuple)
    lock_hash: str = ""
    wagering_executed: bool = False

    def __post_init__(self) -> None:
        if self.wagering_executed:
            raise ValueError("SHADOW_BOUNDARY_VIOLATION: wagering execution is prohibited")
        if not 0.0 <= self.predicted_probability <= 1.0:
            raise ValueError("INVALID_PROBABILITY")
        if not 0.0 <= self.market_probability <= 1.0:
            raise ValueError("INVALID_MARKET_PROBABILITY")
        if datetime.fromisoformat(self.observed_at_utc.replace("Z", "+00:00")) >= datetime.fromisoformat(
            self.event_start_utc.replace("Z", "+00:00")
        ):
            raise ValueError("TEMPORAL_LOCK_VIOLATION")

    def sign(self) -> "PredictionRecord":
        payload = {k: v for k, v in self.__dict__.items() if k != "lock_hash"}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return PredictionRecord(**{**payload, "lock_hash": digest})

    def verify_lock(self) -> bool:
        payload = {k: v for k, v in self.__dict__.items() if k != "lock_hash"}
        expected = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return expected == self.lock_hash


class PredictionBatchEngine:
    """Generates independent shadow predictions in parallel without shared mutable state."""

    def __init__(self, model_version: str = "shadow-v1", max_workers: int = 8) -> None:
        self.model_version = model_version
        self.max_workers = max_workers

    def _generate_one(self, snapshot: MarketSnapshot, selection: str, cycle_id: str) -> PredictionRecord:
        market_probs = FanDuelSnapshotAdapter.normalized_probabilities(snapshot)
        market_probability = market_probs[selection]
        # Baseline model is deliberately conservative: market probability shrunk toward 0.5.
        predicted = 0.5 + 0.85 * (market_probability - 0.5)
        record = PredictionRecord(
            prediction_id=f"pred_{cycle_id}_{snapshot.event_id}_{selection}",
            cycle_id=cycle_id,
            event_id=snapshot.event_id,
            market=snapshot.market,
            selection=selection,
            model_version=self.model_version,
            predicted_probability=predicted,
            market_probability=market_probability,
            observed_at_utc=snapshot.observed_at_utc,
            event_start_utc=snapshot.event_start_utc,
        )
        return record.sign()

    def generate(self, snapshots: Iterable[MarketSnapshot], cycle_id: str) -> list[PredictionRecord]:
        tasks = [(snapshot, selection) for snapshot in snapshots for selection in snapshot.prices]
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures = [pool.submit(self._generate_one, snapshot, selection, cycle_id) for snapshot, selection in tasks]
            return [future.result() for future in futures]

    @staticmethod
    def build_parlay(parent_id: str, legs: Iterable[PredictionRecord]) -> PredictionRecord:
        leg_list = list(legs)
        if not leg_list:
            raise ValueError("PARLAY_REQUIRES_LEGS")
        if any(not leg.verify_lock() for leg in leg_list):
            raise ValueError("PARLAY_REQUIRES_VALID_LEG_LOCKS")
        combined_probability = 1.0
        for leg in leg_list:
            combined_probability *= leg.predicted_probability
        first = leg_list[0]
        # Include each leg's stable prediction identity in the parent selection so
        # different combinations remain distinguishable in every canonical identity
        # surface, not only through the parlay prediction_id.
        parlay_selection = " + ".join(
            f"{leg.event_id}:{leg.selection}" for leg in leg_list
        )
        parlay = PredictionRecord(
            prediction_id=f"parlay_{parent_id}",
            cycle_id=first.cycle_id,
            event_id=first.event_id,
            market="parlay",
            selection=parlay_selection,
            model_version=first.model_version,
            predicted_probability=combined_probability,
            market_probability=1.0,
            observed_at_utc=first.observed_at_utc,
            event_start_utc=first.event_start_utc,
            is_oos=all(leg.is_oos for leg in leg_list),
            is_parlay=True,
            parent_prediction_id=parent_id,
            legs=tuple(leg.prediction_id for leg in leg_list),
        )
        return parlay.sign()
