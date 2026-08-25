"""Tests for Fleet Qualification Ledger."""

import pytest
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
