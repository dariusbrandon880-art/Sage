"""Read-Only Sports/RCE Observability Adapter for SAGE Airspace.

Connects SAGE Airspace observability directly to Sports/RCE longitudinal ledgers
without mutating Sports/RCE core architecture or introducing wagering claims.

The adapter exposes the canonical multi-sport boundary for observability only.
Prediction authority remains in Sports/RCE; Airspace does not create a second
prediction engine or synthetic observation source.
"""

from typing import Dict, Any, Optional, Tuple
from sage.experimental.flight_record import SAGEFlightRecordManager
from sage.experimental.airspace.models import Mission, StationID


CANONICAL_SPORT_COMPETITIONS: Dict[str, Tuple[str, ...]] = {
    "baseball": ("MLB",),
    "basketball": ("NBA", "WNBA", "NCAAB"),
    "football": ("NFL", "NCAAF"),
    "hockey": ("NHL",),
    "tennis": ("ATP", "WTA"),
    "soccer": (),  # extensible domestic/international/tournament competitions
}


class SportsRCEAirspaceAdapter:
    """Read-only adapter translating Sports/RCE ledgers into Airspace C2 views."""

    def __init__(self, flight_record_manager: Optional[SAGEFlightRecordManager] = None):
        self.manager = flight_record_manager or SAGEFlightRecordManager()

    @staticmethod
    def validate_competition(sport: str, competition: str) -> bool:
        """Validate a competition against the canonical sport boundary.

        Soccer is intentionally extensible because its domestic, international,
        and tournament competitions are registered by concrete runtime adapters.
        Unknown competitions fail closed rather than being silently reclassified.
        """
        normalized_sport = str(sport).strip().lower()
        normalized_competition = str(competition).strip().upper()
        if normalized_sport == "soccer":
            return bool(normalized_competition)
        return normalized_competition in CANONICAL_SPORT_COMPETITIONS.get(normalized_sport, ())

    @classmethod
    def canonical_boundary(cls) -> Dict[str, Any]:
        """Return a deterministic, read-only representation of the sport boundary."""
        return {
            "sports": {
                sport: list(competitions)
                for sport, competitions in sorted(CANONICAL_SPORT_COMPETITIONS.items())
            },
            "rules": [
                "REUSE_EXISTING_SPORTS_RCE",
                "NO_DUPLICATE_PREDICTION_ENGINE",
                "NO_SYNTHETIC_PRODUCTION_OBSERVATIONS",
                "FAIL_CLOSED_UNKNOWN_COMPETITION",
                "AIRSPACE_READ_ONLY",
            ],
        }

    def get_sports_mission_state(self) -> Mission:
        """Returns the standard Sports/RCE Mission domain object for Airspace."""
        return Mission(
            mission_id="RCE-002.1",
            mission_name="Durable Longitudinal Prediction Registry",
            theater="Sports/RCE",
            priority="P0",
            objective="Observe real-world public sports events, enforce pre-game temporal locking, and evaluate calibration without real-money wagering.",
            authorized_scope=["public_sports_apis", "temporal_lock_receipts", "longitudinal_calibration"],
            constraints=["ZERO_REAL_MONEY_WAGERING", "IMMUTABLE_PREGAME_LOCK", "STRICT_FAIL_CLOSED"],
            assigned_stations=[StationID.INTEL_STATION, StationID.ENGINEERING_FLIGHT],
            status="ACTIVE",
            success_conditions=["Pre-game temporal lock verified", "Brier calibration score computed post-event"],
            failure_conditions=["Post-event prediction alteration attempt", "Missing observation timestamp"],
            evidence_requirements=["evidence_capture/sports_real_predictions_ledger.json", "evidence_capture/sports_real_flight_001.json"],
            current_frontier="Continuous outcome resolution and Brier score tracking",
        )

    def get_sports_theater_summary(self) -> Dict[str, Any]:
        """Queries underlying Sports/RCE ledger and returns read-only Airspace telemetry summary."""
        sports_report = self.manager.generate_report_view("FULL_24_HOUR_SPORTS_RCE_RESULTS_REPORT")
        unresolved_report = self.manager.generate_report_view("OPEN_UNRESOLVED_RECORDS")

        records = sports_report.get("records", [])
        unresolved_records = unresolved_report.get("records", [])

        resolved_count = sum(1 for r in records if r.get("outcome_status") in ("WIN", "LOSS", "PUSH"))
        parlay_count = sum(1 for r in records if r.get("prediction_classification") == "RESEARCH-ONLY PARLAY")

        latest_evidence = "evidence_capture/sports_real_predictions_ledger.json"
        if records:
            latest_rec = records[-1]
            latest_evidence = f"pred_id:{latest_rec.get('prediction_id')} (event:{latest_rec.get('event_id')})"

        return {
            "theater": "Sports/RCE",
            "active_mission_id": "RCE-002.1",
            "recent_24h_predictions": len(records),
            "unresolved_predictions_count": len(unresolved_records),
            "resolved_predictions_count": resolved_count,
            "research_parlay_count": parlay_count,
            "latest_evidence_ref": latest_evidence,
            "governance_status": "LANE_ISOLATED_ZERO_REAL_MONEY",
            "canonical_boundary": self.canonical_boundary(),
        }
