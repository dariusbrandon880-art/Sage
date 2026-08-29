"""Unit and integration tests for Organism Growth Rate Big Jump Wave."""

import json
import subprocess
from pathlib import Path

from sage.c2.workflow_velocity import MultiSessionVelocityEngine
from sage.experimental.airspace.fleet_evolution import FleetEvolutionIntelligence
from sage.experimental.sports_rce import SportsRCEResearchEngine


def test_organism_growth_rate_calculation():
    fleet_intel = FleetEvolutionIntelligence(commit_sha="a" * 40)
    receipt = fleet_intel.evaluate_organism_growth_rate(
        velocity_score=1.0,
        prediction_accuracy_score=0.9,
        wave_completion_rate=1.0,
        anti_drift_compliance_score=1.0,
    )
    assert receipt.compound_growth_index == 0.975
    assert receipt.growth_verdict == "ACCELERATING"
    assert len(receipt.provenance_hash) == 64


def test_organism_growth_rate_blocked_on_protected_violations():
    fleet_intel = FleetEvolutionIntelligence(commit_sha="b" * 40)
    receipt = fleet_intel.evaluate_organism_growth_rate(
        velocity_score=1.0,
        prediction_accuracy_score=1.0,
        wave_completion_rate=1.0,
        anti_drift_compliance_score=1.0,
        protected_path_violations=1,
    )
    assert receipt.compound_growth_index == 0.0
    assert receipt.growth_verdict == "BLOCKED"


def test_daily_prediction_growth_delta():
    rce_engine = SportsRCEResearchEngine()
    delta = rce_engine.evaluate_daily_prediction_growth_delta(
        historical_brier=0.25, current_brier=0.15, calibration_slope=1.0
    )
    assert delta["brier_delta"] == 0.1
    assert delta["prediction_accuracy_score"] > 0.8
    assert delta["calibration_score"] == 1.0


def test_organism_growth_wave_execution_runner():
    res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    head_sha = res.stdout.strip()

    evidence_file = Path("evidence_capture/organism_growth_wave_evidence.json")
    assert evidence_file.exists()

    with open(evidence_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    import re
    assert re.fullmatch(r"[0-9a-fA-F]{40}", data["exact_git_head"])
    assert re.fullmatch(r"[0-9a-fA-F]{40}", head_sha)
    assert data["wave_id"] == "wave_organism_growth_001"
    assert data["reconvergence_verdict"] == "PASS"
    assert data["status"] == "VALIDATED"
    assert data["organism_growth_receipt"]["growth_verdict"] == "ACCELERATING"
