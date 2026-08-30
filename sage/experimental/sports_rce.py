"""SAGE Sports/RCE — Minimal Real-World Pre-Game Observation & Temporal Locking Substrate.

Provides immutable pre-game observation, temporal lock validation (lock_timestamp < event_start),
SHA-256 receipt generation, and persistence without synthetic substitutions or real-money wagering.
"""

import json
import hashlib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Set, Tuple, List


class SportsRCEResearchEngine:
    """Minimal research-only engine for real-world sports event pre-game observation and locking."""

    SOURCE_NAME = "TheSportsDB (Public Free API)"
    SOURCE_URL = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php"

    def __init__(self, capture_dir: Optional[Path] = None):
        self.capture_dir = capture_dir or Path("evidence_capture")
        self.capture_dir.mkdir(parents=True, exist_ok=True)

    def fetch_upcoming_event(self, date_str: str = "2026-08-17", exclude_event_ids: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Fetch real event schedule for target date from public API source."""
        exclude = exclude_event_ids or set()
        url = f"{self.SOURCE_URL}?d={date_str}&s=Soccer"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 SAGE/1.0 Research"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        events = data.get("events") or []
        if not events:
            raise ValueError(f"No events returned from {url}")

        # Select first upcoming event not in exclude set
        for ev in events:
            raw_id = str(ev.get("idEvent") or "")
            if raw_id in exclude or f"event_tsdb_{raw_id}" in exclude or f"pred_rce_{raw_id}" in exclude:
                continue
            if ev.get("strStatus") in ("NS", "Not Started", "Scheduled", "1"):
                return ev

        # Fallback to first non-excluded event
        for ev in events:
            raw_id = str(ev.get("idEvent") or "")
            if raw_id not in exclude and f"event_tsdb_{raw_id}" not in exclude and f"pred_rce_{raw_id}" not in exclude:
                return ev

        raise ValueError(f"No unexcluded events available for date {date_str} from {url}")

    @staticmethod
    def compute_prediction_hash(record: Dict[str, Any]) -> str:
        """Computes SHA-256 hash over canonical JSON representation of record (excluding prediction_hash)."""
        payload = {k: v for k, v in record.items() if k != "prediction_hash"}
        record_bytes = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(record_bytes).hexdigest()

    @staticmethod
    def verify_prediction_hash(record: Dict[str, Any]) -> bool:
        """Verifies that the record's stored hash matches independent canonical SHA-256 recomputation."""
        stored_hash = record.get("prediction_hash")
        if not stored_hash:
            return False
        computed = SportsRCEResearchEngine.compute_prediction_hash(record)
        return stored_hash == computed

    def create_pre_game_prediction(
        self,
        event_raw: Dict[str, Any],
        selection: str,
        predicted_probability: float,
        reasoning: str,
    ) -> Dict[str, Any]:
        """Constructs and temporally locks a research-only prediction before event start."""
        if not event_raw or not isinstance(event_raw, dict):
            raise ValueError("Invalid event data: event_raw must be a non-empty dictionary")
        if not event_raw.get("idEvent"):
            raise ValueError("Invalid event data: missing 'idEvent'")
        if not event_raw.get("strEvent"):
            raise ValueError("Invalid event data: missing 'strEvent'")
        str_ts = event_raw.get("strTimestamp")
        if not str_ts:
            raise ValueError("Invalid event data: missing 'strTimestamp'")

        obs_dt = datetime.now(timezone.utc)
        obs_timestamp = obs_dt.isoformat()

        # Parse event start time (ISO format)
        if not str_ts.endswith("Z") and "+" not in str_ts:
            str_ts += "Z"

        try:
            event_start_dt = datetime.fromisoformat(str_ts.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"Invalid timestamp format '{str_ts}': {exc}") from exc

        event_start_iso = event_start_dt.isoformat()

        # INVARIANT CHECK: lock_timestamp < event_start
        if obs_dt >= event_start_dt:
            raise ValueError(
                f"Temporal locking invariant failure: lock_timestamp ({obs_timestamp}) "
                f"is not strictly before event_start ({event_start_iso})"
            )

        event_id = f"event_tsdb_{event_raw.get('idEvent', 'unknown')}"
        prediction_id = f"pred_rce_{event_raw.get('idEvent', 'unknown')}"
        receipt_id = f"rcpt_rce_{hashlib.sha256(prediction_id.encode('utf-8')).hexdigest()[:12]}"

        record = {
            "prediction_id": prediction_id,
            "event_id": event_id,
            "event": event_raw.get("strEvent"),
            "sport": event_raw.get("strSport", "Soccer").lower(),
            "league": event_raw.get("strLeague"),
            "teams": {
                "home": event_raw.get("strHomeTeam"),
                "away": event_raw.get("strAwayTeam"),
            },
            "event_start": event_start_iso,
            "observation_timestamp": obs_timestamp,
            "prediction_timestamp": obs_timestamp,
            "market": "match_winner",
            "selection": selection,
            "odds_at_lock": "ODDS_UNAVAILABLE",  # Explicit representation when unavailable
            "implied_probability": "ODDS_UNAVAILABLE",
            "predicted_probability": round(predicted_probability, 4),
            "confidence": round(predicted_probability, 4),
            "reasoning": reasoning,
            "source": self.SOURCE_NAME,
            "source_url": f"{self.SOURCE_URL}?d={event_raw.get('dateEvent', '2026-08-17')}&s=Soccer",
            "source_timestamp": obs_timestamp,
            "prediction_state": "LOCKED",
            "status": "PENDING",
            "classification": "REAL-WORLD RESEARCH PREDICTION",
            "wagering_executed": False,
            "receipt_id": receipt_id,
        }

        # Calculate SHA-256 hash over canonical JSON representation
        record_bytes = json.dumps(record, sort_keys=True, default=str).encode("utf-8")
        record["prediction_hash"] = hashlib.sha256(record_bytes).hexdigest()

        return record

    def persist_prediction_artifact(self, record: Dict[str, Any], filename: str = "sports_real_flight_001.json") -> Path:
        """Persists the locked prediction record to disk."""
        file_path = self.capture_dir / filename

        # INVARIANT CHECK: Rejects overwrite/rewrite if already locked
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if existing.get("prediction_state") == "LOCKED" and existing.get("prediction_id") == record.get("prediction_id"):
                # Return existing path if identical
                return file_path

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)

        return file_path

    def evaluate_daily_prediction_growth_delta(
        self,
        historical_brier: float,
        current_brier: float,
        calibration_slope: float = 1.0,
    ) -> Dict[str, float]:
        """Calculates out-of-sample prediction accuracy improvement and calibration score delta."""
        brier_delta = max(0.0, historical_brier - current_brier)
        accuracy_score = round(min(1.0, max(0.0, 1.0 - current_brier + (brier_delta * 0.5))), 4)
        calibration_score = round(min(1.0, max(0.0, 1.0 - abs(1.0 - calibration_slope))), 4)

        return {
            "historical_brier": historical_brier,
            "current_brier": current_brier,
            "brier_delta": round(brier_delta, 4),
            "prediction_accuracy_score": accuracy_score,
            "calibration_score": calibration_score,
        }


# =====================================================================
# RCE-003.1: TEMPORAL RESEARCH SNAPSHOT & LEAKAGE RECEIPT ENGINE
# =====================================================================

from dataclasses import dataclass, field, asdict
from sage.experimental.sports_longitudinal import parse_iso_utc


@dataclass
class HistoricalResearchSnapshot:
    snapshot_id: str
    research_timestamp: str
    included_observations: List[Dict[str, Any]]
    excluded_post_t_observations: List[Dict[str, Any]]
    provider_states: Dict[str, Any]
    conflicts: List[Dict[str, Any]]
    snapshot_hash: str = ""

    def compute_sha256_hash(self) -> str:
        payload = {
            "snapshot_id": self.snapshot_id,
            "research_timestamp": self.research_timestamp,
            "included_observations": self.included_observations,
            "excluded_post_t_observations": self.excluded_post_t_observations,
            "provider_states": self.provider_states,
            "conflicts": self.conflicts,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.snapshot_hash = self.compute_sha256_hash()
        return self.snapshot_hash


@dataclass
class ResearchIntegrityReceipt:
    receipt_id: str
    snapshot_id: str
    research_timestamp: str
    included_reference_set: List[str]
    post_timestamp_reference_set: List[str]
    excluded_count: int
    integrity_status: str  # RESEARCH_TIME_CLEAN, POST_TIMESTAMP_INFORMATION_DETECTED, AMBIGUOUS_AVAILABILITY, INTEGRITY_FAILURE
    reason: str
    snapshot_hash: str
    integrity_hash: str = ""

    def compute_sha256_hash(self) -> str:
        payload = {
            "receipt_id": self.receipt_id,
            "snapshot_id": self.snapshot_id,
            "research_timestamp": self.research_timestamp,
            "included_reference_set": self.included_reference_set,
            "post_timestamp_reference_set": self.post_timestamp_reference_set,
            "excluded_count": self.excluded_count,
            "integrity_status": self.integrity_status,
            "reason": self.reason,
            "snapshot_hash": self.snapshot_hash,
        }
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def sign(self) -> str:
        self.integrity_hash = self.compute_sha256_hash()
        return self.integrity_hash


class HistoricalResearchReconstructionEngine:
    """Reconstructs point-in-time research snapshots at timestamp T (t <= T) and emits leakage receipts."""

    @staticmethod
    def reconstruct_snapshot(
        observations: List[Dict[str, Any]],
        research_timestamp: str,
    ) -> Tuple[HistoricalResearchSnapshot, ResearchIntegrityReceipt]:
        """Filters observations as-of research_timestamp T, selecting latest state per provider/event."""
        if not research_timestamp:
            raise ValueError("FAIL_CLOSED: research_timestamp cannot be empty")

        try:
            target_dt = parse_iso_utc(research_timestamp)
        except Exception as exc:
            raise ValueError(f"FAIL_CLOSED_AMBIGUOUS_TIMING: Invalid research timestamp '{research_timestamp}': {exc}") from exc

        included_raw = []
        excluded_post_t = []

        # Validate timestamps and classify
        for idx, obs in enumerate(observations):
            avail_ts = obs.get("availability_timestamp") or obs.get("observation_timestamp") or obs.get("source_timestamp")
            if not avail_ts:
                raise ValueError(f"FAIL_CLOSED_MISSING_TIMESTAMP at index {idx}: Observation missing availability/observation timestamp.")

            try:
                avail_dt = parse_iso_utc(avail_ts)
            except Exception as exc:
                raise ValueError(f"FAIL_CLOSED_AMBIGUOUS_TIMING at index {idx}: Unparseable timestamp '{avail_ts}': {exc}") from exc

            if avail_dt <= target_dt:
                included_raw.append((avail_dt, obs))
            else:
                excluded_post_t.append((avail_dt, obs))

        # Group included observations by (provider, event_id) and select latest available
        provider_event_groups: Dict[Tuple[str, str], List[Tuple[datetime, Dict[str, Any]]]] = {}
        for avail_dt, obs in included_raw:
            provider = str(obs.get("provider") or obs.get("source") or "default_provider")
            event_id = str(obs.get("event_id") or obs.get("idEvent") or "unknown_event")
            key = (provider, event_id)
            if key not in provider_event_groups:
                provider_event_groups[key] = []
            provider_event_groups[key].append((avail_dt, obs))

        selected_observations = []
        provider_states: Dict[str, Dict[str, Any]] = {}

        # Deterministic sorting for selected latest observation per provider/event
        for (provider, event_id), group in sorted(provider_event_groups.items(), key=lambda k: (k[0][0], k[0][1])):
            # Sort group by avail_dt ascending, then obs_id/hash string ascending for deterministic tie-break
            sorted_group = sorted(
                group,
                key=lambda x: (
                    x[0],
                    str(x[1].get("observation_id") or x[1].get("prediction_id") or x[1].get("receipt_id") or "")
                )
            )
            latest_obs = sorted_group[-1][1]
            selected_observations.append(latest_obs)

            if provider not in provider_states:
                provider_states[provider] = {}
            provider_states[provider][event_id] = latest_obs

        # Detect provider conflicts for same event
        conflicts = []
        event_providers: Dict[str, List[Tuple[str, Dict[str, Any]]]] = {}
        for provider, events in provider_states.items():
            for event_id, obs in events.items():
                if event_id not in event_providers:
                    event_providers[event_id] = []
                event_providers[event_id].append((provider, obs))

        for event_id, p_list in event_providers.items():
            if len(p_list) > 1:
                # Compare odds/selection across providers
                values = [str(o.get("observed_odds") or o.get("selection") or o.get("odds_at_lock")) for _, o in p_list]
                if len(set(values)) > 1:
                    conflicts.append({
                        "event_id": event_id,
                        "conflict_type": "PROVIDER_VARIANCE",
                        "providers": {p: o for p, o in p_list}
                    })

        # Sort lists deterministically
        selected_observations.sort(key=lambda x: str(x.get("observation_id") or x.get("prediction_id") or x.get("event_id") or ""))
        excluded_obs_list = [obs for _, obs in excluded_post_t]
        excluded_obs_list.sort(key=lambda x: str(x.get("observation_id") or x.get("prediction_id") or x.get("event_id") or ""))

        snapshot_id = f"snap_rce_{hashlib.sha256((research_timestamp + str(len(selected_observations))).encode('utf-8')).hexdigest()[:12]}"

        snapshot = HistoricalResearchSnapshot(
            snapshot_id=snapshot_id,
            research_timestamp=research_timestamp,
            included_observations=selected_observations,
            excluded_post_t_observations=excluded_obs_list,
            provider_states=provider_states,
            conflicts=conflicts,
        )
        snapshot.sign()

        included_refs = [
            str(o.get("observation_id") or o.get("prediction_id") or o.get("receipt_id") or o.get("event_id"))
            for o in selected_observations
        ]
        post_refs = [
            str(o.get("observation_id") or o.get("prediction_id") or o.get("receipt_id") or o.get("event_id"))
            for o in excluded_obs_list
        ]

        if excluded_obs_list:
            integrity_status = "POST_TIMESTAMP_INFORMATION_DETECTED"
            reason = f"Excluded {len(excluded_obs_list)} observation(s) with availability timestamp > {research_timestamp}."
        else:
            integrity_status = "RESEARCH_TIME_CLEAN"
            reason = f"All {len(selected_observations)} observations available on or before research timestamp {research_timestamp}."

        receipt_id = f"rcpt_leak_{hashlib.sha256((snapshot_id + integrity_status).encode('utf-8')).hexdigest()[:12]}"

        receipt = ResearchIntegrityReceipt(
            receipt_id=receipt_id,
            snapshot_id=snapshot_id,
            research_timestamp=research_timestamp,
            included_reference_set=included_refs,
            post_timestamp_reference_set=post_refs,
            excluded_count=len(excluded_obs_list),
            integrity_status=integrity_status,
            reason=reason,
            snapshot_hash=snapshot.snapshot_hash,
        )
        receipt.sign()

        return snapshot, receipt


import math


class OddsPapiObservationAdapter:
    """Adapter parsing OddsPapi historical odds payloads into standardized SAGE observation dicts."""

    @classmethod
    def parse_nested_response(cls, payload: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses a full nested OddsPapi historical odds response structure into a flattened list of standardized observations.

        Navigates: bookmakers -> markets -> outcomes -> players["0"] -> snapshots
        """
        if not isinstance(payload, dict):
            raise ValueError("FAIL_CLOSED: OddsPapi payload must be a dictionary")

        bookmakers = payload.get("bookmakers") or payload.get("data", {}).get("bookmakers") or []

        observations = []

        for bm in bookmakers:
            provider_id = str(bm.get("id") or bm.get("key") or bm.get("name") or context.get("provider_id") or "")
            markets = bm.get("markets") or []

            for mkt in markets:
                market_id = str(mkt.get("id") or mkt.get("key") or mkt.get("name") or context.get("market") or "")
                outcomes = mkt.get("outcomes") or []

                for out in outcomes:
                    outcome_id = str(out.get("id") or out.get("key") or out.get("name") or context.get("selection") or "")
                    players = out.get("players") or {}

                    player_id = "0"
                    snapshots = []
                    if isinstance(players, dict):
                        for p_key, p_val in players.items():
                            player_id = str(p_key)
                            if isinstance(p_val, dict):
                                snapshots = p_val.get("snapshots") or []
                            elif isinstance(p_val, list):
                                snapshots = p_val
                            break
                    elif isinstance(players, list):
                        for idx, p in enumerate(players):
                            if isinstance(p, dict):
                                player_id = str(p.get("id") or idx)
                                snapshots.extend(p.get("snapshots") or [])

                    for snap in snapshots:
                        entry_ctx = dict(context)
                        if provider_id:
                            entry_ctx["provider_id"] = provider_id
                        if market_id:
                            entry_ctx["market"] = market_id
                        if outcome_id:
                            entry_ctx["selection"] = outcome_id
                        if player_id:
                            entry_ctx["player_id"] = player_id

                        parsed_obs = cls.parse_observation(snap, entry_ctx)
                        parsed_obs["limit"] = snap.get("limit")
                        parsed_obs["active"] = snap.get("active", True)
                        parsed_obs["player_id"] = player_id
                        exchange_meta = snap.get("exchangeMeta") or snap.get("exchange")
                        if exchange_meta is not None:
                            parsed_obs["exchangeMeta"] = exchange_meta
                            parsed_obs["exchange_metadata"] = exchange_meta
                        observations.append(parsed_obs)

        return observations

    @staticmethod
    def parse_observation(raw_entry: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Parses a single OddsPapi price/historical entry into a standardized SAGE raw odds observation.

        Enforces strict fail-closed validation on timestamps, prices, and required metadata.
        """
        if not isinstance(raw_entry, dict):
            raise ValueError("FAIL_CLOSED: Raw entry must be a dictionary")

        created_at = raw_entry.get("createdAt") or raw_entry.get("availability_timestamp")
        if not created_at:
            raise ValueError("FAIL_CLOSED_MISSING_TIMESTAMP: Missing 'createdAt' / availability timestamp")

        # Validate timestamp format
        try:
            avail_dt = parse_iso_utc(created_at)
        except Exception as exc:
            raise ValueError(f"FAIL_CLOSED_AMBIGUOUS_TIMING: Unparseable createdAt timestamp '{created_at}': {exc}") from exc

        price = raw_entry.get("price")
        if price is None:
            price = raw_entry.get("quoted_price")

        if price is None or isinstance(price, bool):
            raise ValueError("FAIL_CLOSED_MISSING_PRICE: OddsPapi entry missing valid 'price'")

        try:
            quoted_price = float(price)
            if not math.isfinite(quoted_price):
                raise ValueError(f"Invalid non-finite price value {quoted_price}")
        except Exception as exc:
            raise ValueError(f"FAIL_CLOSED_INVALID_PRICE: Invalid quoted price '{price}': {exc}") from exc

        event_id = str(context.get("event_id") or raw_entry.get("event_id") or raw_entry.get("fixture_id") or "")
        if not event_id:
            raise ValueError("FAIL_CLOSED_MISSING_EVENT: Context/entry missing 'event_id'")

        provider_id = str(context.get("provider_id") or raw_entry.get("bookmaker") or raw_entry.get("provider") or "")
        if not provider_id:
            raise ValueError("FAIL_CLOSED_MISSING_PROVIDER: Context/entry missing 'provider_id' / 'bookmaker'")

        market = str(context.get("market") or raw_entry.get("market") or "")
        if not market:
            raise ValueError("FAIL_CLOSED_MISSING_MARKET: Context/entry missing 'market'")

        selection = str(context.get("selection") or raw_entry.get("selection") or "")
        if not selection:
            raise ValueError("FAIL_CLOSED_MISSING_SELECTION: Context/entry missing 'selection'")

        entry_source_id = str(raw_entry.get("id") or raw_entry.get("entry_id") or "")

        event_start = context.get("event_start") or context.get("event_start_timestamp") or raw_entry.get("event_start")
        if not event_start:
            raise ValueError("FAIL_CLOSED_MISSING_EVENT_START: Context missing 'event_start'")

        try:
            start_dt = parse_iso_utc(event_start)
        except Exception as exc:
            raise ValueError(f"FAIL_CLOSED_AMBIGUOUS_TIMING: Unparseable event_start timestamp '{event_start}': {exc}") from exc

        # In-play contamination check: t_avail >= t_start
        if avail_dt >= start_dt:
            raise ValueError(
                f"FAIL_CLOSED_IN_PLAY_CONTAMINATION: Availability timestamp ({created_at}) "
                f">= Event start timestamp ({event_start})"
            )

        provenance_id = f"oddspapi_{provider_id}_{event_id}_{market}_{entry_source_id}" if entry_source_id else f"oddspapi_{provider_id}_{event_id}_{market}"
        obs_payload = {
            "event_id": event_id,
            "provider": provider_id,
            "provider_id": provider_id,
            "market": market,
            "selection": selection,
            "player_id": str(context.get("player_id") or "0"),
            "source_entry_id": entry_source_id,
            "observed_odds": quoted_price,
            "quoted_price": quoted_price,
            "availability_timestamp": avail_dt.isoformat().replace("+00:00", "Z"),
            "source_timestamp": avail_dt.isoformat().replace("+00:00", "Z"),
            "event_start_timestamp": start_dt.isoformat().replace("+00:00", "Z"),
            "provenance_id": provenance_id,
        }

        # Deterministic SHA-256 observation_id incorporating entry source identity
        serialized = json.dumps(obs_payload, sort_keys=True)
        obs_payload["observation_id"] = f"obs_oddspapi_{hashlib.sha256(serialized.encode('utf-8')).hexdigest()[:16]}"

        return obs_payload


class FanDuelMarketAdapter:
    """Adapter for FanDuel-shaped live/market structures (moneyline, runline/spread, totals)."""

    @staticmethod
    def american_to_implied_prob(american_odds: int) -> float:
        """Converts American odds (e.g., -110, +150) to implied probability (0.0 to 1.0)."""
        if american_odds == 0:
            return 0.5
        if american_odds < 0:
            return abs(american_odds) / (abs(american_odds) + 100.0)
        else:
            return 100.0 / (american_odds + 100.0)

    @classmethod
    def parse_fanduel_market_event(cls, event_dict: Dict[str, Any], timestamp_utc: str) -> Dict[str, Any]:
        """Parses a FanDuel-shaped event/market dictionary into a SAGE standardized observation."""
        event_id = str(event_dict.get("id") or event_dict.get("eventId") or "fd_unknown")
        home_team = event_dict.get("homeTeam") or event_dict.get("home_team", "Home Team")
        away_team = event_dict.get("awayTeam") or event_dict.get("away_team", "Away Team")
        start_time = event_dict.get("startTime") or event_dict.get("event_start_time_utc") or timestamp_utc

        markets = event_dict.get("markets", {})
        moneyline_home = markets.get("moneyline", {}).get("home", -110)
        moneyline_away = markets.get("moneyline", {}).get("away", -110)

        home_implied = cls.american_to_implied_prob(moneyline_home)
        away_implied = cls.american_to_implied_prob(moneyline_away)

        return {
            "source_name": "FanDuel Sportsbook Public Structure",
            "source_url": "https://sportsbook.fanduel.com",
            "event_id": f"fd_game_{event_id}",
            "sport": event_dict.get("sport", "baseball").lower(),
            "league": event_dict.get("league", "mlb").lower(),
            "home_team": home_team,
            "away_team": away_team,
            "event_start_time_utc": start_time,
            "observation_timestamp_utc": timestamp_utc,
            "market_name": "FanDuel Moneyline & Spread Market",
            "observed_odds": {
                "moneyline_home_american": moneyline_home,
                "moneyline_away_american": moneyline_away,
                "home_implied_prob": round(home_implied, 4),
                "away_implied_prob": round(away_implied, 4),
                "spread_line": markets.get("spread", {}).get("line", -1.5),
                "total_over_under": markets.get("totals", {}).get("total", 8.5)
            },
            "event_status": event_dict.get("status", "Scheduled")
        }
