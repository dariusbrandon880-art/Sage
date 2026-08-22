"""Tests for semantic capability lineage reconciliation."""

from sage.capability_lineage import CapabilityLineage, CapabilityLineageIndex


def test_lineage_tracks_historical_to_current_capability():
    index = CapabilityLineageIndex([
        CapabilityLineage(
            historical_concept="ACR continuity bridge",
            current_capability_id="CAP-CONTINUITY-BRIDGE",
            implementation_paths=["sage/acr"],
            evidence_paths=["tests/test_continuity_bridge.py"],
            status="VALIDATED",
        )
    ])

    matches = index.for_capability("CAP-CONTINUITY-BRIDGE")
    assert len(matches) == 1
    assert matches[0].historical_concept == "ACR continuity bridge"
    assert index.unresolved() == []


def test_lineage_exposes_duplicate_and_unresolved_reconciliation_work():
    index = CapabilityLineageIndex([
        CapabilityLineage(historical_concept="old A", current_capability_id="CAP-X", status="STALE_CONFLICTING"),
        CapabilityLineage(historical_concept="old B", current_capability_id="CAP-X", status="READY_FRONTIER"),
    ])

    assert index.duplicate_current_ids() == ["CAP-X"]
    assert len(index.unresolved()) == 2
