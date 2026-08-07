"""SAGE Capability Improvement Measurement (CIM) Framework.

Operates strictly within experimental/non-runtime boundaries to compare
validated capability runs over time and determine improvement.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MetricValue(BaseModel):
    """Represents a single measured metric value with baseline comparison."""
    metric_name: str
    current_value: float
    baseline_value: Optional[float] = None
    difference: Optional[float] = None
    higher_is_better: bool = True
    classification: str = "INCOMPARABLE"  # e.g., IMPROVED, STABLE, REGRESSED, INCOMPARABLE
    provenance_source: str = "unknown"


class CapabilityMeasurementRecord(BaseModel):
    """High-fidelity representation of a Capability Improvement Measurement."""
    capability_id: str
    run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    evidence_artifacts: list[str] = Field(default_factory=list)
    baseline_run_id: Optional[str] = None
    metrics: dict[str, MetricValue] = Field(default_factory=dict)
    overall_classification: str = "INCOMPARABLE"  # e.g., IMPROVED, STABLE, REGRESSED, INCOMPARABLE
    provenance_details: dict[str, Any] = Field(default_factory=dict)


class CapabilityMeasurementEngine:
    """Computes comparable capability measurements against established baselines."""

    def __init__(self, storage_dir: str = "evidence_capture"):
        self.storage_dir = Path(storage_dir)

    def extract_metrics_from_phase4(self, evidence_data: Dict[str, Any]) -> Dict[str, float]:
        """Extracts existing Phase 4 metrics from evidence files for comparison."""
        metrics_extracted = {}

        # Check scenario-level metrics
        if "metrics" in evidence_data:
            m = evidence_data["metrics"]
            if "efficiency" in m:
                metrics_extracted["sage_assisted_duration_mins"] = m["efficiency"].get("sage_assisted_duration_mins")
                metrics_extracted["steps_reduced"] = m["efficiency"].get("steps_reduced")
                metrics_extracted["review_effort_reduction_percent"] = m["efficiency"].get("review_effort_reduction_percent")
            if "governance" in m:
                metrics_extracted["validation_checks_completed"] = m["governance"].get("validation_checks_completed")
                metrics_extracted["blocked_unauthorized_actions"] = m["governance"].get("blocked_unauthorized_actions")
            if "evidence" in m:
                metrics_extracted["completeness_score"] = m["evidence"].get("completeness_score")
                metrics_extracted["traceability_score"] = m["evidence"].get("traceability_score")

        # Check aggregate metrics
        elif "aggregate_metrics" in evidence_data:
            m = evidence_data["aggregate_metrics"]
            metrics_extracted["total_steps_reduced"] = m.get("total_steps_reduced")
            metrics_extracted["overall_efficiency_improvement_percent"] = m.get("overall_efficiency_improvement_percent")
            metrics_extracted["unauthorized_actions_blocked"] = m.get("unauthorized_actions_blocked")
            metrics_extracted["context_recovery_success_rate"] = m.get("context_recovery_success_rate")

        # Strip None values
        return {k: float(v) for k, val in metrics_extracted.items() if (v := val) is not None}

    def compare_runs(
        self,
        capability_id: str,
        current_data: Dict[str, Any],
        baseline_data: Optional[Dict[str, Any]] = None,
        higher_is_better_map: Optional[Dict[str, bool]] = None
    ) -> CapabilityMeasurementRecord:
        """Compare current run metrics against baseline data and generate record."""
        current_run_id = current_data.get("run_identifier") or current_data.get("evaluation_id") or "current_run"
        baseline_run_id = None
        if baseline_data:
            baseline_run_id = baseline_data.get("run_identifier") or baseline_data.get("evaluation_id") or "baseline_run"

        current_metrics = self.extract_metrics_from_phase4(current_data)
        baseline_metrics = self.extract_metrics_from_phase4(baseline_data) if baseline_data else {}

        # Default direction map (higher is better for almost everything except duration)
        dir_map = {
            "sage_assisted_duration_mins": False,
        }
        if higher_is_better_map:
            dir_map.update(higher_is_better_map)

        metrics_comparison = {}
        improved_count = 0
        regressed_count = 0
        stable_count = 0
        incomparable_count = 0

        # Calculate metrics
        all_metric_keys = set(current_metrics.keys()) | set(baseline_metrics.keys())
        for key in all_metric_keys:
            current_val = current_metrics.get(key)
            baseline_val = baseline_metrics.get(key)

            higher_better = dir_map.get(key, True)

            if current_val is None:
                # Metric missing in current run
                metrics_comparison[key] = MetricValue(
                    metric_name=key,
                    current_value=0.0,
                    classification="INCOMPARABLE",
                    provenance_source="missing_current"
                )
                incomparable_count += 1
                continue

            if baseline_val is None:
                # Baseline missing for this metric
                metrics_comparison[key] = MetricValue(
                    metric_name=key,
                    current_value=current_val,
                    classification="INCOMPARABLE",
                    provenance_source="missing_baseline"
                )
                incomparable_count += 1
                continue

            # Compare values
            diff = current_val - baseline_val

            if current_val == baseline_val:
                classification = "STABLE"
                stable_count += 1
            elif (diff > 0 and higher_better) or (diff < 0 and not higher_better):
                classification = "IMPROVED"
                improved_count += 1
            else:
                classification = "REGRESSED"
                regressed_count += 1

            metrics_comparison[key] = MetricValue(
                metric_name=key,
                current_value=current_val,
                baseline_value=baseline_val,
                difference=round(diff, 3),
                higher_is_better=higher_better,
                classification=classification,
                provenance_source="calculated"
            )

        # Determine overall classification
        # Never declare IMPROVED when no valid baseline exists (or all are incomparable)
        if not baseline_data or len(baseline_metrics) == 0:
            overall = "INCOMPARABLE"
        elif regressed_count > 0:
            overall = "REGRESSED"
        elif improved_count > 0:
            overall = "IMPROVED"
        elif stable_count > 0:
            overall = "STABLE"
        else:
            overall = "INCOMPARABLE"

        evidence_artifacts = []
        if "evaluation_id" in current_data:
            evidence_artifacts.append(f"evidence_capture/{current_data['evaluation_id']}.json")

        return CapabilityMeasurementRecord(
            capability_id=capability_id,
            run_id=current_run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            evidence_artifacts=evidence_artifacts,
            baseline_run_id=baseline_run_id,
            metrics=metrics_comparison,
            overall_classification=overall,
            provenance_details={
                "metric_counts": {
                    "improved": improved_count,
                    "regressed": regressed_count,
                    "stable": stable_count,
                    "incomparable": incomparable_count
                }
            }
        )

    def generate_and_save_report(
        self,
        capability_id: str,
        current_data: Dict[str, Any],
        baseline_data: Optional[Dict[str, Any]] = None,
        output_name: str = "capability_improvement_measurement_report.json"
    ) -> str:
        """Helper to generate and save the report as evidence."""
        record = self.compare_runs(capability_id, current_data, baseline_data)
        out_path = self.storage_dir / output_name

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record.model_dump(), f, indent=2)

        print(f"[+] Successfully generated Capability Improvement Measurement report: {out_path}")
        return str(out_path)
