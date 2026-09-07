"""Diversified daily shadow portfolio construction for the Sports/RCE lane."""

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping, Sequence
import hashlib

from .ingestion import MarketSnapshot
from .prediction import PredictionBatchEngine, PredictionRecord

SUPPORTED_SPORTS = frozenset({"MLB", "NBA", "NFL", "NHL"})
MIN_PARLAY_LEGS = 3
MAX_PARLAY_LEGS = 6
DEFAULT_DAILY_TARGET = 50


@dataclass(frozen=True)
class DailyPortfolio:
    cycle_id: str
    records: tuple[PredictionRecord, ...]
    duplicate_rejections: int
    sport_counts: dict[str, int]
    single_count: int
    parlay_count: int
    target: int

    @property
    def count(self) -> int:
        return len(self.records)

    @property
    def target_met(self) -> bool:
        return self.count >= self.target


class DailySportsPortfolioEngine:
    """Build a high-volume, non-duplicated, multi-sport shadow prediction portfolio."""

    def __init__(self, target: int = DEFAULT_DAILY_TARGET, min_parlay_legs: int = MIN_PARLAY_LEGS, max_parlay_legs: int = MAX_PARLAY_LEGS, parlay_share: float = 0.30, max_workers: int = 8) -> None:
        if target < 1:
            raise ValueError("INVALID_DAILY_TARGET")
        if not MIN_PARLAY_LEGS <= min_parlay_legs <= max_parlay_legs <= MAX_PARLAY_LEGS:
            raise ValueError("INVALID_PARLAY_LEG_RANGE")
        if not 0.0 <= parlay_share <= 1.0:
            raise ValueError("INVALID_PARLAY_SHARE")
        self.target = target
        self.min_parlay_legs = min_parlay_legs
        self.max_parlay_legs = max_parlay_legs
        self.parlay_share = parlay_share
        self.batch_engine = PredictionBatchEngine(max_workers=max_workers)

    @staticmethod
    def _sport(snapshot: MarketSnapshot) -> str:
        return snapshot.sport.upper()

    @staticmethod
    def _identity(record: PredictionRecord) -> tuple[str, str, str, str, str, str]:
        return (record.event_id, record.canonical_market_type, record.selection.strip().lower(), record.canonical_line_value, record.model_version, record.observed_at_utc)

    @classmethod
    def _dedupe(cls, records: Iterable[PredictionRecord]) -> tuple[list[PredictionRecord], int]:
        seen: set[tuple[str, str, str, str, str, str]] = set()
        unique: list[PredictionRecord] = []
        rejected = 0
        for record in records:
            key = cls._identity(record)
            if key in seen:
                rejected += 1
                continue
            seen.add(key)
            unique.append(record)
        return unique, rejected

    @staticmethod
    def _select_diverse_singles(records: Sequence[PredictionRecord], target: int, sport_by_event: Mapping[str, str] | None = None) -> list[PredictionRecord]:
        """Select singles round-robin by event while rotating market types.

        Feed order is not allowed to let an early league or market exhaust the daily
        target. The deterministic selector first distributes records across every
        available event and rotates the market index by event position, then consumes
        additional records in the same event-diverse order until the requested single
        count is reached.
        """
        if target <= 0:
            return []

        by_event: dict[str, list[PredictionRecord]] = {}
        for record in records:
            by_event.setdefault(record.event_id, []).append(record)

        if sport_by_event:
            events_by_sport: dict[str, list[str]] = {}
            for event_id in sorted(by_event):
                sport = sport_by_event.get(event_id, "UNKNOWN").upper()
                events_by_sport.setdefault(sport, []).append(event_id)

            ordered_event_ids: list[str] = []
            sports = sorted(events_by_sport)
            max_events = max(len(evs) for evs in events_by_sport.values()) if events_by_sport else 0
            for idx in range(max_events):
                for sport in sports:
                    ev_list = events_by_sport[sport]
                    if idx < len(ev_list):
                        ordered_event_ids.append(ev_list[idx])
            event_ids = ordered_event_ids
        else:
            event_ids = sorted(by_event)

        if not event_ids:
            return []

        selected: list[PredictionRecord] = []
        selected_keys: set[tuple[str, str, str, str, str, str]] = set()
        round_index = 0
        while len(selected) < target:
            made_progress = False
            for event_position, event_id in enumerate(event_ids):
                event_records = by_event[event_id]
                if round_index >= len(event_records):
                    continue
                record_index = (event_position + round_index) % len(event_records)
                record = event_records[record_index]
                key = DailySportsPortfolioEngine._identity(record)
                if key in selected_keys:
                    for candidate in event_records:
                        candidate_key = DailySportsPortfolioEngine._identity(candidate)
                        if candidate_key not in selected_keys:
                            record = candidate
                            key = candidate_key
                            break
                    else:
                        continue
                selected.append(record)
                selected_keys.add(key)
                made_progress = True
                if len(selected) >= target:
                    break
            if not made_progress:
                break
            round_index += 1

        return selected

    def _build_parlays(self, singles: Sequence[PredictionRecord], target_parlays: int) -> list[PredictionRecord]:
        if target_parlays <= 0:
            return []
        by_event: dict[str, list[PredictionRecord]] = {}
        for record in singles:
            by_event.setdefault(record.event_id, []).append(record)
        event_representatives = [legs[0] for _, legs in sorted(by_event.items())]
        parlays: list[PredictionRecord] = []
        seen_combinations: set[tuple[str, ...]] = set()
        for leg_count in range(self.min_parlay_legs, self.max_parlay_legs + 1):
            if len(event_representatives) < leg_count:
                continue
            for combo in combinations(event_representatives, leg_count):
                leg_ids = tuple(leg.prediction_id for leg in combo)
                if leg_ids in seen_combinations:
                    continue
                seen_combinations.add(leg_ids)
                parent_material = "|".join(leg_ids)
                digest = hashlib.sha256(parent_material.encode("utf-8")).hexdigest()[:32]
                parent_id = f"daily-{digest}"
                parlays.append(self.batch_engine.build_parlay(parent_id, combo))
                if len(parlays) >= target_parlays:
                    return parlays
        return parlays

    def build(self, snapshots: Iterable[MarketSnapshot], cycle_id: str) -> DailyPortfolio:
        snapshot_list = list(snapshots)
        invalid_sports = sorted({self._sport(s) for s in snapshot_list if self._sport(s) not in SUPPORTED_SPORTS})
        if invalid_sports:
            raise ValueError(f"UNSUPPORTED_SPORTS: {','.join(invalid_sports)}")
        if not snapshot_list:
            raise ValueError("NO_MARKET_SNAPSHOTS")
        generated = self.batch_engine.generate(snapshot_list, cycle_id)
        singles, duplicate_rejections = self._dedupe(generated)
        sport_by_event = {snapshot.event_id: self._sport(snapshot) for snapshot in snapshot_list}
        target_parlays = min(int(round(self.target * self.parlay_share)), max(0, self.target - 1))
        parlays = self._build_parlays(singles, target_parlays)
        remaining = max(0, self.target - len(parlays))
        selected_singles = self._select_diverse_singles(singles, remaining, sport_by_event)
        records = selected_singles + parlays[: max(0, self.target - len(selected_singles))]
        if len(records) < self.target:
            raise ValueError(f"DAILY_TARGET_UNMET: requested={self.target} available={len(records)}")
        sport_counts: dict[str, int] = {sport: 0 for sport in sorted(SUPPORTED_SPORTS)}
        for record in records:
            sport = sport_by_event.get(record.event_id)
            if sport in sport_counts:
                sport_counts[sport] += 1
        return DailyPortfolio(cycle_id=cycle_id, records=tuple(records), duplicate_rejections=duplicate_rejections, sport_counts=sport_counts, single_count=sum(not r.is_parlay for r in records), parlay_count=sum(r.is_parlay for r in records), target=self.target)
