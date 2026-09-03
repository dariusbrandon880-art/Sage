"""Tests for the legacy Fleet Qualification snapshot/recovery boundary."""

import json

import pytest

from sage.experimental.airspace.fleet_qualification_ledger import FleetQualificationLedger


def test_direct_xp_rank_mutation_is_fail_closed():
    ledger = FleetQualificationLedger()

    with pytest.raises(RuntimeError, match="Direct FleetQualificationLedger XP mutation is disabled"):
        ledger.record_xp_event(agent_id="agent-alpha", xp_gained=150, badge="badge-cql")

    state = ledger.get_or_create_state("agent-alpha")
    assert state.total_xp == 0
    assert state.rank_title == "Cadet"
    assert state.cql_qualified is False
    assert state.sql_qualified is False
    assert state.verification_badges == []


def test_snapshot_export_and_recovery_preserves_historical_state_without_recalculation():
    snapshot = json.dumps(
        {
            "timestamp": 0,
            "agents": {
                "agent-1": {
                    "agent_id": "agent-1",
                    "rank_title": "Flight Captain",
                    "total_xp": 200,
                    "cql_qualified": False,
                    "sql_qualified": False,
                    "verification_badges": ["badge-1"],
                    "last_updated": 0,
                },
                "agent-2": {
                    "agent_id": "agent-2",
                    "rank_title": "Fleet Commander",
                    "total_xp": 1200,
                    "cql_qualified": True,
                    "sql_qualified": True,
                    "verification_badges": ["badge-2"],
                    "last_updated": 0,
                },
            },
        }
    )

    ledger = FleetQualificationLedger()
    assert ledger.recover_from_snapshot(snapshot) == 2

    state1 = ledger.get_or_create_state("agent-1")
    assert state1.rank_title == "Flight Captain"
    assert state1.total_xp == 200

    state2 = ledger.get_or_create_state("agent-2")
    assert state2.rank_title == "Fleet Commander"
    assert state2.total_xp == 1200
    assert state2.cql_qualified is True
    assert state2.sql_qualified is True

    exported = json.loads(ledger.export_snapshot())
    assert exported["agents"]["agent-1"]["rank_title"] == "Flight Captain"
    assert exported["agents"]["agent-2"]["rank_title"] == "Fleet Commander"
