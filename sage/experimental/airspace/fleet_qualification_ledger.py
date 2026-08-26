"""Fleet Qualification Ledger & State Recovery Engine.

Preserves current-main state persistence/recovery while adding Session 2
qualification records and evidence-bound rank summaries.
"""
from __future__ import annotations
import hashlib, json, time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class FleetRankState(BaseModel):
    agent_id: str
    rank_title: str = "Cadet"
    total_xp: int = 0
    cql_qualified: bool = False
    sql_qualified: bool = False
    verification_badges: List[str] = Field(default_factory=list)
    last_updated: float = Field(default_factory=time.time)

class QualificationRecord(BaseModel):
    record_id: str
    station_id: str
    agent_id: str
    rank_title: str
    qualifications: List[str] = Field(default_factory=list)
    xp_earned: int = 0
    evidence_receipt_hashes: List[str] = Field(default_factory=list)
    issued_at: float = Field(default_factory=time.time)
    record_hash: str = ""
    def compute_hash(self) -> str:
        payload = {"record_id": self.record_id, "station_id": self.station_id, "agent_id": self.agent_id, "rank_title": self.rank_title, "qualifications": sorted(self.qualifications), "xp_earned": self.xp_earned, "evidence_receipt_hashes": sorted(self.evidence_receipt_hashes)}
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

class FleetQualificationLedger:
    RANK_THRESHOLDS = [(1000, "Fleet Admiral"), (500, "Commander"), (250, "Lieutenant Commander"), (100, "Lieutenant"), (0, "Flight Officer")]
    def __init__(self):
        self._states: Dict[str, FleetRankState] = {}
        self._records: Dict[str, QualificationRecord] = {}
    def get_or_create_state(self, agent_id: str) -> FleetRankState:
        if agent_id not in self._states:
            self._states[agent_id] = FleetRankState(agent_id=agent_id)
        return self._states[agent_id]
    def record_xp_event(self, agent_id: str, xp_gained: int, badge: Optional[str] = None) -> FleetRankState:
        state = self.get_or_create_state(agent_id)
        state.total_xp += xp_gained
        if badge and badge not in state.verification_badges:
            state.verification_badges.append(badge)
        if state.total_xp >= 1000:
            state.rank_title, state.cql_qualified, state.sql_qualified = "Fleet Commander", True, True
        elif state.total_xp >= 500:
            state.rank_title, state.cql_qualified = "Squadron Leader", True
        elif state.total_xp >= 100:
            state.rank_title = "Flight Captain"
        state.last_updated = time.time()
        return state
    def issue_qualification(self, station_id: str, agent_id: str, qualifications: List[str], xp_earned: int, evidence_receipt_hashes: Optional[List[str]] = None) -> QualificationRecord:
        rank = next(title for threshold, title in self.RANK_THRESHOLDS if xp_earned >= threshold)
        record = QualificationRecord(record_id=f"qual-{agent_id}-{time.time_ns()}", station_id=station_id, agent_id=agent_id, rank_title=rank, qualifications=qualifications, xp_earned=xp_earned, evidence_receipt_hashes=evidence_receipt_hashes or [])
        record.record_hash = record.compute_hash()
        self._records[record.record_id] = record
        return record
    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        records = [r for r in self._records.values() if r.agent_id == agent_id]
        if not records:
            return {"agent_id": agent_id, "rank_title": "Unranked", "total_xp": 0, "qualifications": [], "record_count": 0}
        total_xp = sum(r.xp_earned for r in records)
        rank = next(title for threshold, title in self.RANK_THRESHOLDS if total_xp >= threshold)
        return {"agent_id": agent_id, "rank_title": rank, "total_xp": total_xp, "qualifications": sorted({q for r in records for q in r.qualifications}), "record_count": len(records)}
    def export_snapshot(self) -> str:
        return json.dumps({"timestamp": time.time(), "agents": {k: v.model_dump() for k, v in self._states.items()}}, indent=2)
    def recover_from_snapshot(self, snapshot_json: str) -> int:
        data = json.loads(snapshot_json)
        restored = 0
        for agent_id, state in data.get("agents", {}).items():
            self._states[agent_id] = FleetRankState(**state)
            restored += 1
        return restored
