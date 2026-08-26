"""Unit tests for Fleet Qualification Ledger & State Recovery Engine."""

from sage.experimental.airspace.fleet_qualification_ledger import FleetQualificationLedger


def test_fleet_qualification_xp_and_rank_progression():
    ledger = FleetQualificationLedger()
    state1 = ledger.record_xp_event("agent-alpha", 150, "badge-cql")
    assert state1.rank_title == "Flight Captain"
    assert "badge-cql" in state1.verification_badges
    state2 = ledger.record_xp_event("agent-alpha", 400, "badge-sql")
    assert state2.rank_title == "Squadron Leader"
    assert state2.cql_qualified is True
    state3 = ledger.record_xp_event("agent-alpha", 500)
    assert state3.rank_title == "Fleet Commander"
    assert state3.sql_qualified is True


def test_qualification_record_issuance_and_summary():
    ledger = FleetQualificationLedger()
    record = ledger.issue_qualification(
        station_id="STATION_ALPHA",
        agent_id="agent-beta",
        qualifications=["QUAL-F2"],
        xp_earned=250,
        evidence_receipt_hashes=["hash-f2"],
    )
    assert record.rank_title == "Lieutenant Commander"
    assert len(record.record_hash) == 64
    summary = ledger.get_agent_summary("agent-beta")
    assert summary["total_xp"] == 250
    assert summary["qualifications"] == ["QUAL-F2"]
    assert summary["record_count"] == 1


def test_snapshot_export_and_recovery_preserves_records():
    original = FleetQualificationLedger()
    original.record_xp_event("agent-1", 200, "badge-1")
    original.issue_qualification("STATION_ALPHA", "agent-2", ["QUAL-F2"], 250, ["hash-2"])
    snapshot = original.export_snapshot()
    recovered = FleetQualificationLedger()
    count = recovered.recover_from_snapshot(snapshot)
    assert count == 2
    assert recovered.get_or_create_state("agent-1").rank_title == "Flight Captain"
    assert recovered.get_agent_summary("agent-2")["record_count"] == 1
