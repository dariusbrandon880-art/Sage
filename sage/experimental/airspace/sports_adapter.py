"""Read-only Sports/RCE observability adapter for SAGE Airspace.

This adapter exposes existing Sports/RCE state to C2/Airspace without creating a
second sports engine. Evidence references are descriptive and are never treated
as proof of empirical acceptance by themselves.
"""

from typing import Any, Dict, Optional
from sage.experimental.flight_record import SAGEFlightRecordManager
from sage.experimental.airspace.models import Mission, StationID


class SportsRCEAirspaceAdapter:
    """Read-only adapter translating Sports/RCE ledgers into Airspace C2 views."""

    def __init__(self, flight_record_manager: Optional[SAGEFlightRecordManager] = None):
        self.manager = flight_record_manager or SAGEFlightRecordManager()

    def get_sports_mission_state(self) -> Mission:
        return Mission(
            mission_id="RCE-002.1",
            mission_name="Durable Longitudinal Prediction Registry",
            theater="Sports/RCE",
            priority="P0",
            objective="Observe public sports events, enforce pre-game temporal locking, and evaluate calibration without real-money wagering.",
            authorized_scope=["public_sports_apis", "temporal_lock_receipts", "longitudinal_calibration"],
            constraints=["ZERO_REAL_MONEY_WAGERING", "IMMUTABLE_PREGAME_LOCK", "STRICT_FAIL_CLOSED"],
            assigned_stations=[StationID.INTEL_STATION, StationID.ENGINEERING_FLIGHT],
            status="ACTIVE",
            success_conditions=["Pre-game temporal lock verified", "Brier calibration score computed post-event"],
            failure_conditions=["Post-event prediction alteration attempt", "Missing observation timestamp"],
            evidence_requirements=["canonical sports forecast receipt", "independently sourced outcome receipt"],
            current_frontier="Continuous outcome resolution and Brier score tracking",
        )

    def get_sports_theater_summary(self) -> Dict[str, Any]:
        """Return read-only telemetry; missing/invalid evidence is not converted to ACCEPTED."""
        sports_report = self.manager.generate_report_view("FULL_24_HOUR_SPORTS_RCE_RESULTS_REPORT")
        unresolved_report = self.manager.generate_report_view("OPEN_UNRESOLVED_RECORDS")
        records = sports_report.get("records", [])
        unresolved_records = unresolved_report.get("records", [])

        resolved_count = sum(1 for r in records if r.get("outcome_status") in ("WIN", "LOSS", "PUSH"))
        parlay_count = sum(1 for r in records if r.get("prediction_classification") == "RESEARCH-ONLY PARLAY")

        latest_evidence = None
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
            "empirical_acceptance": "NOT_ASSERTED",
        }
