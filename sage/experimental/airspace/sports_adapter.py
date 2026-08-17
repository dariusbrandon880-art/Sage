"""Read-Only Sports/RCE Observability Adapter for SAGE Airspace.

Connects SAGE Airspace observability directly to Sports/RCE longitudinal ledgers
and RCE-002.4 Evidence Drift Monitor without mutating Sports/RCE core architecture.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from sage.experimental.flight_record import SAGEFlightRecordManager
from sage.experimental.airspace.models import Mission, Sortie, SortieState, StationID
from sage.experimental.sports_rce import ObservationDriftMonitor, ObservationDriftClassification


class SportsRCEAirspaceAdapter:
    """Read-only adapter translating Sports/RCE prediction ledgers into Airspace C2 state views."""

    def __init__(
        self,
        flight_record_manager: Optional[SAGEFlightRecordManager] = None,
        drift_monitor: Optional[ObservationDriftMonitor] = None,
    ):
        self.manager = flight_record_manager or SAGEFlightRecordManager()
        self.drift_monitor = drift_monitor or ObservationDriftMonitor()

    def get_sports_mission_state(self) -> Mission:
        """Returns standard Sports/RCE Mission domain object for Airspace tracking."""
        return Mission(
            mission_id="RCE-002.1",
            mission_name="Durable Longitudinal Prediction Registry",
            theater="Sports/RCE",
            priority="P0",
            objective="Observe real-world public sports events, enforce pre-game temporal locking, and evaluate calibration without real-money wagering.",
            authorized_scope=["public_sports_apis", "temporal_lock_receipts", "longitudinal_calibration", "evidence_drift_monitoring"],
            constraints=["ZERO_REAL_MONEY_WAGERING", "IMMUTABLE_PREGAME_LOCK", "STRICT_FAIL_CLOSED"],
            assigned_stations=[StationID.INTEL_STATION, StationID.ENGINEERING_FLIGHT],
            status="ACTIVE",
            success_conditions=["Pre-game temporal lock verified", "Brier calibration score computed post-event", "Source evidence drift monitored"],
            failure_conditions=["Post-event prediction alteration attempt", "Missing observation timestamp"],
            evidence_requirements=["evidence_capture/sports_real_predictions_ledger.json", "evidence_capture/sports_real_flight_001.json"],
            current_frontier="Continuous outcome resolution, Brier score tracking, and RCE-002.4 evidence drift monitoring",
        )

    def get_sports_theater_summary(self) -> Dict[str, Any]:
        """Queries underlying Sports/RCE ledger and returns read-only Airspace telemetry summary."""
        sports_report = self.manager.generate_report_view("FULL_24_HOUR_SPORTS_RCE_RESULTS_REPORT")
        unresolved_report = self.manager.generate_report_view("OPEN_UNRESOLVED_RECORDS")

        records = sports_report.get("records", [])
        unresolved_records = unresolved_report.get("records", [])

        # Categorize records
        resolved_count = sum(1 for r in records if r.get("outcome_status") in ("WIN", "LOSS", "PUSH"))
        parlay_count = sum(1 for r in records if r.get("prediction_classification") == "RESEARCH-ONLY PARLAY")

        latest_evidence = "evidence_capture/sports_real_predictions_ledger.json"
        if records:
            latest_rec = records[-1]
            latest_evidence = f"pred_id:{latest_rec.get('prediction_id')} (event:{latest_rec.get('event_id')})"

        # Check evidence drift status from ObservationDriftMonitor
        drift_records = self.drift_monitor._load_ledger()
        drift_status = "OBSERVATION_STABLE"
        if drift_records:
            meaningful_drifts = [r for r in drift_records if r.get("meaningful_semantic_change")]
            conflicts = [r for r in drift_records if r.get("drift_classification") in (
                ObservationDriftClassification.DRIFT_CONFLICT.value,
                ObservationDriftClassification.DRIFT_STAT_CORRECTION.value
            )]
            if conflicts:
                drift_status = "OBSERVATION_REVIEW_REQUIRED"
            elif meaningful_drifts:
                drift_status = "OBSERVATION_DRIFTED"

        return {
            "theater": "Sports/RCE",
            "active_mission_id": "RCE-002.1",
            "recent_24h_predictions": len(records),
            "unresolved_predictions_count": len(unresolved_records),
            "resolved_predictions_count": resolved_count,
            "research_parlay_count": parlay_count,
            "latest_evidence_ref": latest_evidence,
            "evidence_drift_status": drift_status,
            "governance_status": "LANE_ISOLATED_ZERO_REAL_MONEY",
        }
