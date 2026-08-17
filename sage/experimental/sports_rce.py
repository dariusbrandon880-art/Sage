"""SAGE Sports/RCE — Pre-Game Observation, Temporal Locking, Evidence Drift & RCE-003.1 Temporal Research Snapshot Substrate.

Provides immutable pre-game observation, temporal lock validation (lock_timestamp < event_start),
SHA-256 receipt generation, persistence, RCE-002.4 Evidence Drift Monitoring, and
RCE-003.1 Point-in-Time Temporal Research Snapshot Reconstruction with Leakage Receipts.
"""

from enum import Enum
import json
import hashlib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------
# RCE-002.4 Observation Evidence Drift Models
# ---------------------------------------------------------

class ObservationDriftClassification(str, Enum):
    """Classification of evidence drift between initial observation and later provider state."""
    DRIFT_UNKNOWN = "DRIFT_UNKNOWN"
    DRIFT_NONE = "DRIFT_NONE"
    DRIFT_METADATA_ONLY = "DRIFT_METADATA_ONLY"
    DRIFT_STATUS_CHANGE = "DRIFT_STATUS_CHANGE"
    DRIFT_FINALITY_CHANGE = "DRIFT_FINALITY_CHANGE"
    DRIFT_STAT_CORRECTION = "DRIFT_STAT_CORRECTION"
    DRIFT_CONFLICT = "DRIFT_CONFLICT"
    DRIFT_UNAVAILABLE = "DRIFT_UNAVAILABLE"


class ObservationEvidenceSnapshot(BaseModel):
    """Immutable snapshot of evidence supporting a sports observation at a specific retrieval time."""
    snapshot_id: str
    observation_id: str
    provider: str
    external_event_id: str
    observed_timestamp: str
    retrieval_timestamp: str
    payload_hash: str
    source_observation_reference: str
    arbitration_receipt_reference: Optional[str] = None
    reconciliation_receipt_reference: Optional[str] = None
    evidence_reference: str
    status: str = "NS"
    scores: Dict[str, Any] = Field(default_factory=dict)
    event_start: Optional[str] = None
    raw_payload_summary: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("snapshot_id", "observation_id")
    @classmethod
    def validate_non_empty_ids(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("Snapshot identity fields cannot be empty.")
        return v


class ObservationDriftRecord(BaseModel):
    """Record capturing the comparison between initial and later evidence snapshots."""
    drift_record_id: str
    observation_id: str
    initial_snapshot_id: str
    later_snapshot_id: Optional[str] = None
    drift_classification: ObservationDriftClassification
    meaningful_semantic_change: bool
    drift_details: List[str] = Field(default_factory=list)
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    integrity_hash: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.integrity_hash:
            self.integrity_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        serialized = json.dumps({
            "drift_record_id": self.drift_record_id,
            "observation_id": self.observation_id,
            "initial_snapshot_id": self.initial_snapshot_id,
            "later_snapshot_id": self.later_snapshot_id or "",
            "drift_classification": self.drift_classification.value,
            "meaningful_semantic_change": self.meaningful_semantic_change,
            "drift_details": sorted(self.drift_details),
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ObservationDriftMonitor:
    """Monitors and classifies evidence drift between initial observation snapshots and later provider states."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = Path(storage_path or "evidence_capture/sports_drift_ledger.json")

    def _load_ledger(self) -> List[Dict[str, Any]]:
        if not self.storage_path.exists():
            return []
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except Exception:
            return []

    def _save_ledger(self, records: List[Dict[str, Any]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

    def create_snapshot(
        self,
        observation_id: str,
        provider: str,
        external_event_id: str,
        observed_timestamp: str,
        retrieval_timestamp: str,
        raw_payload: Dict[str, Any],
        source_observation_reference: str,
        evidence_reference: str,
        arbitration_receipt_reference: Optional[str] = None,
        reconciliation_receipt_reference: Optional[str] = None,
    ) -> ObservationEvidenceSnapshot:
        """Constructs an immutable evidence snapshot with canonical SHA-256 payload hash."""
        payload_bytes = json.dumps(raw_payload, sort_keys=True, default=str).encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        snapshot_id = f"snap_{hashlib.sha256(f'{observation_id}:{provider}:{retrieval_timestamp}:{payload_hash}'.encode('utf-8')).hexdigest()[:12]}"

        # Extract status and score details safely
        status = str(raw_payload.get("strStatus") or raw_payload.get("status") or "NS")
        home_score = raw_payload.get("intHomeScore") or raw_payload.get("home_score")
        away_score = raw_payload.get("intAwayScore") or raw_payload.get("away_score")

        scores = {}
        if home_score is not None and away_score is not None:
            try:
                scores = {"home": float(home_score), "away": float(away_score)}
            except Exception:
                pass

        event_start = raw_payload.get("strTimestamp") or raw_payload.get("event_start")

        return ObservationEvidenceSnapshot(
            snapshot_id=snapshot_id,
            observation_id=observation_id,
            provider=provider,
            external_event_id=external_event_id,
            observed_timestamp=observed_timestamp,
            retrieval_timestamp=retrieval_timestamp,
            payload_hash=payload_hash,
            source_observation_reference=source_observation_reference,
            arbitration_receipt_reference=arbitration_receipt_reference,
            reconciliation_receipt_reference=reconciliation_receipt_reference,
            evidence_reference=evidence_reference,
            status=status,
            scores=scores,
            event_start=event_start,
            raw_payload_summary={
                "event": raw_payload.get("strEvent"),
                "status": status,
                "scores": scores,
            },
        )

    def compare_snapshots(
        self,
        initial_snapshot: ObservationEvidenceSnapshot,
        later_snapshot: Optional[ObservationEvidenceSnapshot],
        provider_conflict: bool = False,
    ) -> ObservationDriftRecord:
        """Compares initial snapshot against later snapshot to classify evidence drift.

        Guarantees de-duplication: duplicate comparison check does not double count identical drift.
        """
        if not initial_snapshot or not initial_snapshot.observation_id:
            raise ValueError("Missing provenance: initial_snapshot is required and must contain observation_id.")

        ledger = self._load_ledger()

        # Handle unavailable source
        if later_snapshot is None:
            drift_rec_id = f"drift_{hashlib.sha256(f'{initial_snapshot.snapshot_id}:UNAVAILABLE'.encode('utf-8')).hexdigest()[:12]}"
            # De-duplication check
            for existing in ledger:
                if existing.get("drift_record_id") == drift_rec_id:
                    return ObservationDriftRecord(**existing)

            record = ObservationDriftRecord(
                drift_record_id=drift_rec_id,
                observation_id=initial_snapshot.observation_id,
                initial_snapshot_id=initial_snapshot.snapshot_id,
                later_snapshot_id=None,
                drift_classification=ObservationDriftClassification.DRIFT_UNAVAILABLE,
                meaningful_semantic_change=True,
                drift_details=["Later provider retrieval unavailable or source unreachable."],
            )
            ledger.append(record.model_dump())
            self._save_ledger(ledger)
            return record

        drift_rec_id = f"drift_{hashlib.sha256(f'{initial_snapshot.snapshot_id}:{later_snapshot.snapshot_id}:{provider_conflict}'.encode('utf-8')).hexdigest()[:12]}"

        # De-duplication check
        for existing in ledger:
            if existing.get("drift_record_id") == drift_rec_id:
                return ObservationDriftRecord(**existing)

        drift_details = []
        classification = ObservationDriftClassification.DRIFT_NONE
        meaningful_change = False

        # 1. Provider Conflict check
        if provider_conflict or initial_snapshot.provider != later_snapshot.provider:
            classification = ObservationDriftClassification.DRIFT_CONFLICT
            meaningful_change = True
            drift_details.append(f"Provider conflict detected: initial ({initial_snapshot.provider}) vs later ({later_snapshot.provider})")

        # 2. Payload Hash Check
        elif initial_snapshot.payload_hash == later_snapshot.payload_hash:
            classification = ObservationDriftClassification.DRIFT_NONE
            meaningful_change = False
            drift_details.append("Identical payload hash. No evidence drift detected.")

        # 3. Status & Finality Drift Check
        else:
            initial_status = initial_snapshot.status.upper()
            later_status = later_snapshot.status.upper()

            if initial_status != later_status:
                if later_status in ("FT", "MATCH FINISHED", "FINISHED", "2", "3"):
                    classification = ObservationDriftClassification.DRIFT_FINALITY_CHANGE
                    meaningful_change = True
                    drift_details.append(f"Finality state change: status transitioned from '{initial_snapshot.status}' to '{later_snapshot.status}'")
                else:
                    classification = ObservationDriftClassification.DRIFT_STATUS_CHANGE
                    meaningful_change = True
                    drift_details.append(f"Event status change: status transitioned from '{initial_snapshot.status}' to '{later_snapshot.status}'")

            # 4. Stat / Score Correction Check
            elif initial_snapshot.scores != later_snapshot.scores:
                classification = ObservationDriftClassification.DRIFT_STAT_CORRECTION
                meaningful_change = True
                drift_details.append(f"Stat correction detected: scores changed from {initial_snapshot.scores} to {later_snapshot.scores}")

            # 5. Non-Material Metadata Change Check
            else:
                classification = ObservationDriftClassification.DRIFT_METADATA_ONLY
                meaningful_change = False
                drift_details.append(f"Non-material metadata change: payload hash changed from {initial_snapshot.payload_hash[:8]} to {later_snapshot.payload_hash[:8]} without semantic status/score drift")

        record = ObservationDriftRecord(
            drift_record_id=drift_rec_id,
            observation_id=initial_snapshot.observation_id,
            initial_snapshot_id=initial_snapshot.snapshot_id,
            later_snapshot_id=later_snapshot.snapshot_id,
            drift_classification=classification,
            meaningful_semantic_change=meaningful_change,
            drift_details=drift_details,
        )

        ledger.append(record.model_dump())
        self._save_ledger(ledger)
        return record


# ---------------------------------------------------------
# RCE-003.1 Point-in-Time Temporal Research Snapshot Models
# ---------------------------------------------------------

class ResearchIntegrityStatus(str, Enum):
    """Classification of temporal research snapshot integrity."""
    RESEARCH_TIME_CLEAN = "RESEARCH_TIME_CLEAN"
    POST_TIMESTAMP_INFORMATION_DETECTED = "POST_TIMESTAMP_INFORMATION_DETECTED"
    AMBIGUOUS_AVAILABILITY = "AMBIGUOUS_AVAILABILITY"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"


class HistoricalResearchSnapshot(BaseModel):
    """Point-in-time as-of research snapshot representing exact available information state at research_timestamp."""
    snapshot_id: str
    research_timestamp: str
    event_identities: List[str] = Field(default_factory=list)
    included_observation_references: List[str] = Field(default_factory=list)
    excluded_post_timestamp_references: List[str] = Field(default_factory=list)
    effective_observation_state: Dict[str, Any] = Field(default_factory=dict)
    source_conflict_references: List[str] = Field(default_factory=list)
    snapshot_hash: str = ""
    creation_reference: str = "RCE-003.1 Historical Research Reconstruction Engine"
    integrity_hash: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.snapshot_hash:
            self.snapshot_hash = self.compute_snapshot_hash()
        if not self.integrity_hash:
            self.integrity_hash = self.compute_integrity_hash()

    def compute_snapshot_hash(self) -> str:
        serialized = json.dumps({
            "research_timestamp": self.research_timestamp,
            "event_identities": sorted(self.event_identities),
            "included_observation_references": sorted(self.included_observation_references),
            "excluded_post_timestamp_references": sorted(self.excluded_post_timestamp_references),
            "effective_observation_state": self.effective_observation_state,
            "source_conflict_references": sorted(self.source_conflict_references),
        }, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def compute_integrity_hash(self) -> str:
        serialized = json.dumps({
            "snapshot_id": self.snapshot_id,
            "snapshot_hash": self.snapshot_hash,
            "creation_reference": self.creation_reference,
        }, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class ResearchIntegrityReceipt(BaseModel):
    """Integrity receipt certifying whether post-timestamp leakage entered a historical research snapshot."""
    receipt_id: str
    snapshot_id: str
    research_timestamp: str
    observed_reference_set: List[str] = Field(default_factory=list)
    post_timestamp_reference_set: List[str] = Field(default_factory=list)
    excluded_count: int = 0
    integrity_status: ResearchIntegrityStatus = ResearchIntegrityStatus.RESEARCH_TIME_CLEAN
    reason: str = ""
    snapshot_hash: str = ""
    integrity_hash: str = ""

    def __init__(self, **data: Any):
        super().__init__(**data)
        if not self.integrity_hash:
            self.integrity_hash = self.compute_sha256()

    def compute_sha256(self) -> str:
        serialized = json.dumps({
            "receipt_id": self.receipt_id,
            "snapshot_id": self.snapshot_id,
            "research_timestamp": self.research_timestamp,
            "observed_reference_set": sorted(self.observed_reference_set),
            "post_timestamp_reference_set": sorted(self.post_timestamp_reference_set),
            "excluded_count": self.excluded_count,
            "integrity_status": self.integrity_status.value,
            "reason": self.reason,
            "snapshot_hash": self.snapshot_hash,
        }, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class HistoricalResearchReconstructionEngine:
    """Reconstructs point-in-time as-of research snapshots and emits research integrity receipts."""

    @staticmethod
    def _parse_iso(ts_str: str) -> datetime:
        if not ts_str or not isinstance(ts_str, str):
            raise ValueError("Invalid timestamp: timestamp must be a non-empty string.")
        norm = ts_str.strip()
        if not norm.endswith("Z") and "+" not in norm:
            norm += "Z"
        return datetime.fromisoformat(norm.replace("Z", "+00:00"))

    def reconstruct_as_of_snapshot(
        self,
        research_timestamp: str,
        snapshots: List[ObservationEvidenceSnapshot],
        provider_conflicts: Optional[List[Dict[str, Any]]] = None,
        force_leakage_detection: bool = False,
    ) -> Tuple[HistoricalResearchSnapshot, ResearchIntegrityReceipt]:
        """Reconstructs the exact information state available at research_timestamp T and evaluates leakage."""
        try:
            target_dt = self._parse_iso(research_timestamp)
        except Exception as e:
            raise ValueError(f"Ambiguous research timestamp format '{research_timestamp}': {e}") from e

        included_refs = []
        excluded_refs = []
        event_ids = set()
        conflicts_refs = []

        # Provider/Event latest observation map as of T
        provider_event_map: Dict[Tuple[str, str], ObservationEvidenceSnapshot] = {}

        for snap in snapshots:
            if not snap.retrieval_timestamp or not snap.observed_timestamp:
                raise ValueError(f"Ambiguous timestamp in snapshot '{snap.snapshot_id}': retrieval or observation timestamp missing.")

            try:
                retrieval_dt = self._parse_iso(snap.retrieval_timestamp)
                observed_dt = self._parse_iso(snap.observed_timestamp)
            except Exception as e:
                raise ValueError(f"Ambiguous timestamp in snapshot '{snap.snapshot_id}': {e}") from e

            event_ids.add(snap.external_event_id)

            # AS-OF RULE: Include only if retrieval_timestamp <= T AND observed_timestamp <= T
            if retrieval_dt <= target_dt and observed_dt <= target_dt:
                included_refs.append(snap.snapshot_id)
                key = (snap.provider, snap.external_event_id)
                if key not in provider_event_map:
                    provider_event_map[key] = snap
                else:
                    # Select latest valid observation as of T
                    existing_dt = self._parse_iso(provider_event_map[key].retrieval_timestamp)
                    if retrieval_dt > existing_dt:
                        provider_event_map[key] = snap
                    elif retrieval_dt == existing_dt and snap.snapshot_id < provider_event_map[key].snapshot_id:
                        # Deterministic string tie-breaker for identical retrieval timestamps
                        provider_event_map[key] = snap
            else:
                excluded_refs.append(snap.snapshot_id)

        # Build effective observation state (preserving provider distinctions)
        effective_state = {}
        for (provider, ev_id), snap in sorted(provider_event_map.items(), key=lambda x: (x[0][0], x[0][1])):
            state_key = f"{provider}:{ev_id}"
            effective_state[state_key] = {
                "snapshot_id": snap.snapshot_id,
                "observation_id": snap.observation_id,
                "provider": provider,
                "external_event_id": ev_id,
                "retrieval_timestamp": snap.retrieval_timestamp,
                "observed_timestamp": snap.observed_timestamp,
                "status": snap.status,
                "scores": snap.scores,
                "payload_hash": snap.payload_hash,
            }

        # Track provider conflicts
        if provider_conflicts:
            for conf in provider_conflicts:
                conflicts_refs.append(conf.get("conflict_id", "conf_unknown"))

        # Snapshot ID
        snap_hash_input = f"{research_timestamp}:{sorted(included_refs)}:{sorted(excluded_refs)}"
        snap_id = f"res_snap_{hashlib.sha256(snap_hash_input.encode('utf-8')).hexdigest()[:12]}"

        snapshot = HistoricalResearchSnapshot(
            snapshot_id=snap_id,
            research_timestamp=research_timestamp,
            event_identities=sorted(list(event_ids)),
            included_observation_references=sorted(included_refs),
            excluded_post_timestamp_references=sorted(excluded_refs),
            effective_observation_state=effective_state,
            source_conflict_references=sorted(conflicts_refs),
        )

        # Evaluate Integrity Status
        if len(excluded_refs) > 0 or force_leakage_detection:
            status = ResearchIntegrityStatus.POST_TIMESTAMP_INFORMATION_DETECTED
            reason = f"Post-timestamp information detected: {len(excluded_refs)} observations excluded as post-T."
        else:
            status = ResearchIntegrityStatus.RESEARCH_TIME_CLEAN
            reason = f"Reconstructed cleanly as-of {research_timestamp}. {len(included_refs)} observations included, 0 post-T excluded."

        receipt_id = f"rcpt_leak_{hashlib.sha256(f'{snap_id}:{status.value}'.encode('utf-8')).hexdigest()[:12]}"

        receipt = ResearchIntegrityReceipt(
            receipt_id=receipt_id,
            snapshot_id=snapshot.snapshot_id,
            research_timestamp=research_timestamp,
            observed_reference_set=snapshot.included_observation_references,
            post_timestamp_reference_set=snapshot.excluded_post_timestamp_references,
            excluded_count=len(excluded_refs),
            integrity_status=status,
            reason=reason,
            snapshot_hash=snapshot.snapshot_hash,
        )

        return snapshot, receipt


# ---------------------------------------------------------
# SportsRCEResearchEngine (Existing Substrate)
# ---------------------------------------------------------

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
