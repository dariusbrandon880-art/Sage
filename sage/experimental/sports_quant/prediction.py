"""Concurrent paper-prediction generation with immutable pre-event locks."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Iterable, Mapping

from .ingestion import MarketSnapshot, FanDuelSnapshotAdapter


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
        parlay = PredictionRecord(
            prediction_id=f"parlay_{parent_id}",
            cycle_id=first.cycle_id,
            event_id=first.event_id,
            market="parlay",
            selection=" + ".join(leg.selection for leg in leg_list),
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
