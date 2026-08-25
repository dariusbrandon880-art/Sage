"""Unit tests for Fleet Qualification Ledger & State Recovery Engine."""

import json
from sage.experimental.airspace.fleet_qualification_ledger import (
    FleetQualificationLedger,
)


def test_fleet_qualification_xp_and_rank_progression():
    ledger = FleetQualificationLedger()

    state1 = ledger.record_xp_event(agent_id="agent-alpha", xp_gained=150, badge="badge-cql")
    assert state1.rank_title == "Flight Captain"
    assert "badge-cql" in state1.verification_badges

    state2 = ledger.record_xp_event(agent_id="agent-alpha", xp_gained=400, badge="badge-sql")
    assert state2.rank_title == "Squadron Leader"
    assert state2.cql_qualified is True

    state3 = ledger.record_xp_event(agent_id="agent-alpha", xp_gained=500)
    assert state3.rank_title == "Fleet Commander"
    assert state3.sql_qualified is True


def test_snapshot_export_and_recovery():
    ledger_orig = FleetQualificationLedger()
    ledger_orig.record_xp_event("agent-1", 200, "badge-1")
    ledger_orig.record_xp_event("agent-2", 1200, "badge-2")

    snapshot = ledger_orig.export_snapshot()
    assert "agent-1" in snapshot
    assert "agent-2" in snapshot

    ledger_recovered = FleetQualificationLedger()
    count = ledger_recovered.recover_from_snapshot(snapshot)

    assert count == 2
    state1 = ledger_recovered.get_or_create_state("agent-1")
    assert state1.rank_title == "Flight Captain"

    state2 = ledger_recovered.get_or_create_state("agent-2")
    assert state2.rank_title == "Fleet Commander"
    assert state2.cql_qualified is True
    assert state2.sql_qualified is True
