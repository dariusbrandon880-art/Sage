"""Unit tests for Fleet Evolution State Recovery Integration."""

from sage.experimental.airspace.fleet_evolution import FleetEvolutionIntelligence
from sage.experimental.airspace.fleet_qualification_ledger import FleetQualificationLedger


def test_fleet_evolution_recovered_snapshot_evaluation():
    ledger = FleetQualificationLedger()
    ledger.record_xp_event("agent-1", 500, "badge-1")
    ledger.record_xp_event("agent-2", 1200, "badge-2")

    snapshot = ledger.export_snapshot()

    intel = FleetEvolutionIntelligence(commit_sha="db2592167dba5eda4c024bba9202ff085d9c1d9b")
    receipt = intel.evaluate_recovered_ledger_snapshot(snapshot)

    assert receipt.commit_sha == "db2592167dba5eda4c024bba9202ff085d9c1d9b"
    assert receipt.growth_signal == "ACCELERATING"
    assert receipt.growth_index >= 0.8
    assert "flight_quality" in receipt.metrics
