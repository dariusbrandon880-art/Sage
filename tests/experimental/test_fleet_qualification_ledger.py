"""Tests for reconciled Fleet Qualification Ledger."""
from sage.experimental.airspace.fleet_qualification_ledger import FleetQualificationLedger, QualificationRecord

def test_fleet_qualification_xp_and_rank_progression():
    l=FleetQualificationLedger(); s=l.record_xp_event("agent-alpha",150,"badge-cql"); assert s.rank_title=="Flight Captain"; s=l.record_xp_event("agent-alpha",400,"badge-sql"); assert s.rank_title=="Squadron Leader" and s.cql_qualified; s=l.record_xp_event("agent-alpha",500); assert s.rank_title=="Fleet Commander" and s.sql_qualified

def test_snapshot_export_and_recovery():
    l=FleetQualificationLedger(); l.record_xp_event("agent-1",200,"badge-1"); l.record_xp_event("agent-2",1200,"badge-2"); r=FleetQualificationLedger(); assert r.recover_from_snapshot(l.export_snapshot())==2; assert r.get_or_create_state("agent-2").sql_qualified

def test_record_hash_integrity():
    r=QualificationRecord(record_id="r",station_id="S",agent_id="A",rank_title="Commander",qualifications=["CQL"],xp_earned=500); r.record_hash=r.compute_hash(); assert len(r.record_hash)==64 and r.record_hash==r.compute_hash()

def test_qualification_rank_derivation():
    l=FleetQualificationLedger(); assert l.issue_qualification("S","a",["CQL"],50).rank_title=="Flight Officer"; assert l.issue_qualification("S","b",["CQL"],300).rank_title=="Lieutenant Commander"; assert l.issue_qualification("S","c",["FULL"],1200).rank_title=="Fleet Admiral"

def test_agent_summary():
    l=FleetQualificationLedger(); l.issue_qualification("S","j",["CQL"],200); l.issue_qualification("S","j",["SQL","AIRSPACE"],400); s=l.get_agent_summary("j"); assert s["total_xp"]==600 and s["rank_title"]=="Commander" and s["qualifications"]==["AIRSPACE","CQL","SQL"]
