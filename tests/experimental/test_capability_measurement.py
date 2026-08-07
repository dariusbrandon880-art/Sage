"""Unit tests for the SAGE Capability Improvement Measurement (CIM) framework."""

import json
from pathlib import Path
import pytest
from sage.experimental.act.capability_measurement import (
    CapabilityMeasurementEngine,
    CapabilityMeasurementRecord,
    MetricValue
)


def test_cim_missing_baseline():
    """Verify that when no baseline exists, the classification is INCOMPARABLE and never declared as IMPROVED."""
    current = {
        "run_identifier": "run_current_001",
        "metrics": {
            "efficiency": {
                "sage_assisted_duration_mins": 4.5,
                "steps_reduced": 12,
                "review_effort_reduction_percent": 82.5
            }
        }
    }

    engine = CapabilityMeasurementEngine()
    record = engine.compare_runs("CAP-PHASE-4-EVAL", current_data=current, baseline_data=None)

    assert record.overall_classification == "INCOMPARABLE"
    assert record.baseline_run_id is None
    for metric in record.metrics.values():
        assert metric.classification == "INCOMPARABLE"
        assert metric.baseline_value is None


def test_cim_missing_metric():
    """Verify that a missing metric in either baseline or current is cleanly identified and marked INCOMPARABLE."""
    current = {
        "run_identifier": "run_current_001",
        "metrics": {
            "efficiency": {
                "steps_reduced": 12
            }
        }
    }
    baseline = {
        "run_identifier": "run_baseline_001",
        "metrics": {
            "efficiency": {
                "sage_assisted_duration_mins": 5.0,
                "steps_reduced": 10
            }
        }
    }

    engine = CapabilityMeasurementEngine()
    record = engine.compare_runs("CAP-PHASE-4-EVAL", current_data=current, baseline_data=baseline)

    # steps_reduced is comparable, sage_assisted_duration_mins is missing in current
    assert "steps_reduced" in record.metrics
    assert record.metrics["steps_reduced"].classification == "IMPROVED"

    assert "sage_assisted_duration_mins" in record.metrics
    assert record.metrics["sage_assisted_duration_mins"].classification == "INCOMPARABLE"


def test_cim_measurable_improvement():
    """Verify classification of measurable improvement across positive and negative metrics."""
    current = {
        "run_identifier": "run_current_001",
        "metrics": {
            "efficiency": {
                "sage_assisted_duration_mins": 4.0,  # Negative metric: current < baseline (Improved!)
                "steps_reduced": 15,                 # Positive metric: current > baseline (Improved!)
                "review_effort_reduction_percent": 90.0
            }
        }
    }
    baseline = {
        "run_identifier": "run_baseline_001",
        "metrics": {
            "efficiency": {
                "sage_assisted_duration_mins": 6.0,
                "steps_reduced": 10,
                "review_effort_reduction_percent": 80.0
            }
        }
    }

    engine = CapabilityMeasurementEngine()
    record = engine.compare_runs("CAP-PHASE-4-EVAL", current_data=current, baseline_data=baseline)

    assert record.overall_classification == "IMPROVED"
    assert record.metrics["sage_assisted_duration_mins"].classification == "IMPROVED"
    assert record.metrics["steps_reduced"].classification == "IMPROVED"
    assert record.metrics["review_effort_reduction_percent"].classification == "IMPROVED"


def test_cim_measurable_regression():
    """Verify that even a single regression is correctly flagged and regresses the overall classification."""
    current = {
        "run_identifier": "run_current_001",
        "metrics": {
            "efficiency": {
                "sage_assisted_duration_mins": 7.0,  # Negative metric: current > baseline (Regressed!)
                "steps_reduced": 12,                 # Positive metric: current > baseline (Improved!)
                "review_effort_reduction_percent": 85.0
            }
        }
    }
    baseline = {
        "run_identifier": "run_baseline_001",
        "metrics": {
            "efficiency": {
                "sage_assisted_duration_mins": 5.0,
                "steps_reduced": 10,
                "review_effort_reduction_percent": 80.0
            }
        }
    }

    engine = CapabilityMeasurementEngine()
    record = engine.compare_runs("CAP-PHASE-4-EVAL", current_data=current, baseline_data=baseline)

    assert record.overall_classification == "REGRESSED"
    assert record.metrics["sage_assisted_duration_mins"].classification == "REGRESSED"
    assert record.metrics["steps_reduced"].classification == "IMPROVED"


def test_cim_stable_result():
    """Verify stable outcomes when metric values are identical."""
    current = {
        "run_identifier": "run_current_001",
        "metrics": {
            "efficiency": {
                "steps_reduced": 10,
                "review_effort_reduction_percent": 80.0
            }
        }
    }
    baseline = {
        "run_identifier": "run_baseline_001",
        "metrics": {
            "efficiency": {
                "steps_reduced": 10,
                "review_effort_reduction_percent": 80.0
            }
        }
    }

    engine = CapabilityMeasurementEngine()
    record = engine.compare_runs("CAP-PHASE-4-EVAL", current_data=current, baseline_data=baseline)

    assert record.overall_classification == "STABLE"
    assert record.metrics["steps_reduced"].classification == "STABLE"
    assert record.metrics["review_effort_reduction_percent"].classification == "STABLE"


def test_cim_provenance_linkage(tmp_path):
    """Verify evidence and provenance connections in generated records and persisted reports."""
    current = {
        "evaluation_id": "eval_current_report",
        "run_identifier": "run_current_001",
        "metrics": {
            "efficiency": {
                "steps_reduced": 15
            }
        }
    }
    baseline = {
        "evaluation_id": "eval_baseline_report",
        "run_identifier": "run_baseline_001",
        "metrics": {
            "efficiency": {
                "steps_reduced": 10
            }
        }
    }

    engine = CapabilityMeasurementEngine(storage_dir=str(tmp_path))
    report_path = engine.generate_and_save_report(
        capability_id="CAP-PHASE-4-EVAL",
        current_data=current,
        baseline_data=baseline,
        output_name="measurement_report_test.json"
    )

    # Check that report is generated and saved correctly
    saved_file = Path(report_path)
    assert saved_file.exists()

    with open(saved_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["capability_id"] == "CAP-PHASE-4-EVAL"
    assert data["run_id"] == "run_current_001"
    assert data["baseline_run_id"] == "run_baseline_001"
    assert "evidence_capture/eval_current_report.json" in data["evidence_artifacts"]
    assert data["metrics"]["steps_reduced"]["current_value"] == 15.0
    assert data["metrics"]["steps_reduced"]["baseline_value"] == 10.0
    assert data["metrics"]["steps_reduced"]["classification"] == "IMPROVED"
    assert data["overall_classification"] == "IMPROVED"
    assert data["provenance_details"]["metric_counts"]["improved"] == 1
