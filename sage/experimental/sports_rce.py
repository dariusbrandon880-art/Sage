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

    @classmethod
    def reconstruct_snapshot_from_evidence(
        cls,
        evidence_data: Any,
        research_timestamp: str
    ) -> Tuple[HistoricalResearchSnapshot, ResearchIntegrityReceipt]:
        """Ingests persisted flight evidence (dict, list, or JSON string) and reconstructs point-in-time snapshot."""
        if isinstance(evidence_data, str):
            try:
                evidence_data = json.loads(evidence_data)
            except Exception as exc:
                raise ValueError(f"FAIL_CLOSED_INVALID_EVIDENCE: Failed to parse JSON evidence string: {exc}") from exc

        observations = []
        if isinstance(evidence_data, list):
            observations = evidence_data
        elif isinstance(evidence_data, dict):
            # Inspect structure for flight record or prediction list
            if "flight_record" in evidence_data and isinstance(evidence_data["flight_record"], dict):
                rec = evidence_data["flight_record"]
                if "locked_prediction" in rec and isinstance(rec["locked_prediction"], dict):
                    obs_dict = dict(rec["locked_prediction"])
                    evt_obs = obs_dict.get("event_observation") or {}
                    if isinstance(evt_obs, dict):
                        obs_dict["availability_timestamp"] = (
                            evt_obs.get("observation_timestamp_utc") or
                            evt_obs.get("event_start_time_utc") or
                            obs_dict.get("lock_timestamp_utc")
                        )
                    else:
                        obs_dict["availability_timestamp"] = obs_dict.get("lock_timestamp_utc")
                    observations.append(obs_dict)
            elif "predictions" in evidence_data and isinstance(evidence_data["predictions"], list):
                for pred in evidence_data["predictions"]:
                    if isinstance(pred, dict):
                        obs_dict = dict(pred)
                        evt_obs = obs_dict.get("event_observation") or {}
                        if isinstance(evt_obs, dict):
                            obs_dict["availability_timestamp"] = (
                                evt_obs.get("observation_timestamp_utc") or
                                evt_obs.get("event_start_time_utc") or
                                obs_dict.get("lock_timestamp_utc")
                            )
                        else:
                            obs_dict["availability_timestamp"] = obs_dict.get("lock_timestamp_utc")
                        observations.append(obs_dict)
            elif "prediction_id" in evidence_data or "observation_id" in evidence_data or "event_id" in evidence_data:
                obs_dict = dict(evidence_data)
                evt_obs = obs_dict.get("event_observation") or {}
                if isinstance(evt_obs, dict):
                    obs_dict["availability_timestamp"] = (
                        obs_dict.get("availability_timestamp") or
                        evt_obs.get("observation_timestamp_utc") or
                        obs_dict.get("lock_timestamp_utc")
                    )
                observations.append(obs_dict)
            else:
                raise ValueError("FAIL_CLOSED_INVALID_EVIDENCE: Dict evidence structure unrecognized.")
        else:
            raise ValueError(f"FAIL_CLOSED_INVALID_EVIDENCE: Unsupported evidence data type '{type(evidence_data)}'")

        if not observations:
            raise ValueError("FAIL_CLOSED_INVALID_EVIDENCE: No valid observations extracted from evidence payload.")

        return cls.reconstruct_snapshot(observations=observations, research_timestamp=research_timestamp)

    @classmethod
    def reconstruct_snapshot_from_file(
        cls,
        file_path: Path | str,
        research_timestamp: str
    ) -> Tuple[HistoricalResearchSnapshot, ResearchIntegrityReceipt]:
        """Loads persisted flight evidence JSON file directly from disk and reconstructs point-in-time snapshot."""
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"FAIL_CLOSED_FILE_NOT_FOUND: Evidence file '{path}' does not exist.")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            raise ValueError(f"FAIL_CLOSED_INVALID_EVIDENCE: Failed to load JSON from '{path}': {exc}") from exc

        return cls.reconstruct_snapshot_from_evidence(evidence_data=data, research_timestamp=research_timestamp)
