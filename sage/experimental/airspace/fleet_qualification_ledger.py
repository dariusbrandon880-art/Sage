"""Fleet Qualification Ledger & State Recovery Engine.

Maps verified evidence receipts, test proofs, and XP events to military fleet rank states,
providing state persistence, snapshot exporting, qualification record issuing, and recovery.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QualificationRecord(BaseModel):
    """Immutable qualification record binding an agent to verified qualifications."""

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
        payload = {
            "record_id": self.record_id,
            "station_id": self.station_id,
            "agent_id": self.agent_id,
            "rank_title": self.rank_title,
            "qualifications": sorted(self.qualifications),
            "xp_earned": self.xp_earned,
            "evidence_receipt_hashes": sorted(self.evidence_receipt_hashes),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class FleetRankState(BaseModel):
    """Military rank state of an airspace fleet agent."""

    agent_id: str
    rank_title: str = "Cadet"
    total_xp: int = 0
    cql_qualified: bool = False
    sql_qualified: bool = False
    verification_badges: List[str] = Field(default_factory=list)
    last_updated: float = Field(default_factory=time.time)


class FleetQualificationLedger:
    """Ledger tracking fleet qualification states, records, snapshots, and recovery."""

    RANK_THRESHOLDS = [
        (1000, "Fleet Admiral"),
        (500, "Commander"),
        (250, "Lieutenant Commander"),
        (100, "Lieutenant"),
        (0, "Flight Officer"),
    ]

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
            state.rank_title = "Fleet Commander"
            state.cql_qualified = True
            state.sql_qualified = True
        elif state.total_xp >= 500:
            state.rank_title = "Squadron Leader"
            state.cql_qualified = True
        elif state.total_xp >= 100:
            state.rank_title = "Flight Captain"
        state.last_updated = time.time()
        return state

    def issue_qualification(
        self,
        station_id: str,
        agent_id: str,
        qualifications: List[str],
        xp_earned: int,
        evidence_receipt_hashes: Optional[List[str]] = None,
    ) -> QualificationRecord:
        receipts = evidence_receipt_hashes or []
        rank_title = "Flight Officer"
        for threshold, title in self.RANK_THRESHOLDS:
            if xp_earned >= threshold:
                rank_title = title
                break
        record = QualificationRecord(
            record_id=f"qual-{agent_id}-{time.time_ns()}",
            station_id=station_id,
            agent_id=agent_id,
            rank_title=rank_title,
            qualifications=qualifications,
            xp_earned=xp_earned,
            evidence_receipt_hashes=receipts,
        )
        record.record_hash = record.compute_hash()
        self._records[record.record_id] = record
        self.record_xp_event(agent_id, xp_earned, badge=qualifications[0] if qualifications else None)
        return record

    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        records = [r for r in self._records.values() if r.agent_id == agent_id]
        if not records:
            return {"agent_id": agent_id, "rank_title": "Unranked", "total_xp": 0, "qualifications": [], "record_count": 0}
        total_xp = sum(r.xp_earned for r in records)
        qualifications = sorted({q for r in records for q in r.qualifications})
        rank_title = "Flight Officer"
        for threshold, title in self.RANK_THRESHOLDS:
            if total_xp >= threshold:
                rank_title = title
                break
        return {"agent_id": agent_id, "rank_title": rank_title, "total_xp": total_xp, "qualifications": qualifications, "record_count": len(records)}

    def export_snapshot(self) -> str:
        return json.dumps(
            {
                "timestamp": time.time(),
                "agents": {agent_id: state.model_dump() for agent_id, state in self._states.items()},
                "records": {record_id: record.model_dump() for record_id, record in self._records.items()},
            },
            indent=2,
        )

    def recover_from_snapshot(self, snapshot_json: str) -> int:
        data = json.loads(snapshot_json)
        restored_count = 0
        for agent_id, agent_dict in data.get("agents", {}).items():
            self._states[agent_id] = FleetRankState(**agent_dict)
            restored_count += 1
        for record_id, record_dict in data.get("records", {}).items():
            self._records[record_id] = QualificationRecord(**record_dict)
        return restored_count
