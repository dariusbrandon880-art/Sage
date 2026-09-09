"""Diversified daily shadow portfolio construction for the Sports/RCE lane."""

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Mapping, Sequence
import hashlib

from .ingestion import MarketSnapshot, PlayerPropSnapshot
from .prediction import FanDuelPlayerPropAnalyzer, PredictionBatchEngine, PredictionRecord

SUPPORTED_SPORTS = frozenset({"MLB", "NBA", "NFL", "NHL", "SOCCER", "TENNIS"})
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
    def _identity(record: PredictionRecord) -> tuple[str, str, str, str, str]:
        return (record.event_id, record.canonical_market_type, record.selection.strip().lower(), record.canonical_line_value, record.model_version)

    @classmethod
    def _dedupe(cls, records: Iterable[PredictionRecord]) -> tuple[list[PredictionRecord], int]:
        seen: set[tuple[str, str, str, str, str]] = set()
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

    @classmethod
    def _select_singles_round_robin_with_props(cls, singles: Sequence[PredictionRecord], target_singles: int, sport_by_event: Mapping[str, str]) -> list[PredictionRecord]:
        if target_singles <= 0:
            return []
        by_sport_event: dict[str, dict[str, list[PredictionRecord]]] = {}
        for record in singles:
            sport = sport_by_event.get(record.event_id, "UNKNOWN").upper()
            by_sport_event.setdefault(sport, {}).setdefault(record.event_id, []).append(record)

        sports = sorted(by_sport_event.keys())
        events_by_sport = {s: sorted(by_sport_event[s].keys()) for s in sports}
        event_idx_by_sport = {s: 0 for s in sports}

        selected: list[PredictionRecord] = []
        while len(selected) < target_singles:
            any_added = False
            for s in sports:
                if len(selected) >= target_singles:
                    break
                ev_list = events_by_sport[s]
                if not ev_list:
                    continue
                e_idx = event_idx_by_sport[s] % len(ev_list)
                target_eid = ev_list[e_idx]
                pred_list = by_sport_event[s][target_eid]
                if pred_list:
                    selected.append(pred_list.pop(0))
                    any_added = True
                event_idx_by_sport[s] += 1
                if not pred_list:
                    ev_list.remove(target_eid)
            if not any_added:
                break
        return selected

    @classmethod
    def _select_singles_round_robin(cls, singles: Sequence[PredictionRecord], target_singles: int, snapshots: Sequence[MarketSnapshot]) -> list[PredictionRecord]:
        sport_by_event = {s.event_id: cls._sport(s) for s in snapshots}
        return cls._select_singles_round_robin_with_props(singles, target_singles, sport_by_event)

    def build(
        self,
        snapshots: Iterable[MarketSnapshot],
        cycle_id: str,
        prop_snapshots: Iterable[PlayerPropSnapshot] | None = None,
    ) -> DailyPortfolio:
        snapshot_list = list(snapshots)
        prop_list = list(prop_snapshots) if prop_snapshots else []


        all_sports = {self._sport(s) for s in snapshot_list} | {p.sport.upper() for p in prop_list}
        invalid_sports = sorted({s for s in all_sports if s not in SUPPORTED_SPORTS})
        if invalid_sports:
            raise ValueError(f"UNSUPPORTED_SPORTS: {','.join(invalid_sports)}")
        if not snapshot_list and not prop_list:
            raise ValueError("NO_MARKET_SNAPSHOTS")


        generated = self.batch_engine.generate(snapshot_list, cycle_id) if snapshot_list else []
        if prop_list:
            prop_analyzer = FanDuelPlayerPropAnalyzer()
            for p_snap in prop_list:
                edge_res = prop_analyzer.analyze_prop(p_snap)
                prop_rec = prop_analyzer.generate_prop_prediction(p_snap, edge_res, cycle_id=cycle_id)
                generated.append(prop_rec)


        singles, duplicate_rejections = self._dedupe(generated)
        sport_by_event = {snapshot.event_id: self._sport(snapshot) for snapshot in snapshot_list}
        for p in prop_list:
            sport_by_event[p.event_id] = p.sport.upper()
        target_parlays = min(int(round(self.target * self.parlay_share)), max(0, self.target - 1))
        parlays = self._build_parlays(singles, target_parlays)
        remaining_singles = max(0, self.target - len(parlays))
        selected_singles = self._select_singles_round_robin_with_props(singles, remaining_singles, sport_by_event)
        records = selected_singles + parlays[: max(0, self.target - len(selected_singles))]
        if len(records) < self.target:
            raise ValueError(f"DAILY_TARGET_UNMET: requested={self.target} available={len(records)}")
        sport_by_event = {snapshot.event_id: self._sport(snapshot) for snapshot in snapshot_list}
        sport_counts: dict[str, int] = {sport: 0 for sport in sorted(SUPPORTED_SPORTS)}
        for record in records:
            sport = sport_by_event.get(record.event_id)
            if sport in sport_counts:
                sport_counts[sport] += 1
        return DailyPortfolio(cycle_id=cycle_id, records=tuple(records), duplicate_rejections=duplicate_rejections, sport_counts=sport_counts, single_count=sum(not r.is_parlay for r in records), parlay_count=sum(r.is_parlay for r in records), target=self.target)
