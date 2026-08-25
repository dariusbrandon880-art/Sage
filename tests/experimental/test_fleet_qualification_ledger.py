"""Unit tests for Fleet Qualification Ledger & State Recovery Engine."""

import json
from sage.experimental.airspace.fleet_qualification_ledger import (
    FleetQualificationLedger,
    QualificationRecord,
)


def test_qualification_record_hash_integrity():
    record = QualificationRecord(
        record_id="rec-001",
        station_id="STATION_ALPHA",
        agent_id="AGENT_JULES",
        rank_title="Commander",
        qualifications=["CQL-V1", "SQL-V1"],
        xp_earned=500,
        evidence_receipt_hashes=["abc123hash"],
    )
    record.record_hash = record.compute_hash()
    assert len(record.record_hash) == 64
    assert record.record_hash == record.compute_hash()


def test_issue_qualification_rank_derivation():
    ledger = FleetQualificationLedger()

    r1 = ledger.issue_qualification(
        station_id="STATION_ALPHA",
        agent_id="agent_1",
        qualifications=["CQL-V1"],
        xp_earned=50,
    )
    assert r1.rank_title == "Flight Officer"

    r2 = ledger.issue_qualification(
        station_id="STATION_ALPHA",
        agent_id="agent_2",
        qualifications=["CQL-V1", "SQL-V1"],
        xp_earned=300,
    )
    assert r2.rank_title == "Lieutenant Commander"

    r3 = ledger.issue_qualification(
        station_id="STATION_ALPHA",
        agent_id="agent_3",
        qualifications=["FULL-COMMAND"],
        xp_earned=1200,
    )
    assert r3.rank_title == "Fleet Admiral"


def test_get_agent_summary_aggregation():
    ledger = FleetQualificationLedger()

    ledger.issue_qualification(
        station_id="STATION_ALPHA",
        agent_id="agent_jules",
        qualifications=["CQL-V1"],
        xp_earned=200,
    )
    ledger.issue_qualification(
        station_id="STATION_ALPHA",
        agent_id="agent_jules",
        qualifications=["SQL-V1", "AIRSPACE-PRO"],
        xp_earned=400,
    )

    summary = ledger.get_agent_summary("agent_jules")
    assert summary["agent_id"] == "agent_jules"
    assert summary["total_xp"] == 600
    assert summary["rank_title"] == "Commander"
    assert summary["qualifications"] == ["AIRSPACE-PRO", "CQL-V1", "SQL-V1"]
    assert summary["record_count"] == 2


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
