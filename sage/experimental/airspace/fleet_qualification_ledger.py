"""Fleet Qualification Ledger for Military Airspace Governance."""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QualificationRecord(BaseModel):
    """Immutable qualification record binding agent identity to verified military fleet qualifications."""

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
        """Compute SHA-256 fingerprint for qualification record."""
        payload = {
            "record_id": self.record_id,
            "station_id": self.station_id,
            "agent_id": self.agent_id,
            "rank_title": self.rank_title,
            "qualifications": sorted(self.qualifications),
            "xp_earned": self.xp_earned,
            "evidence_receipt_hashes": sorted(self.evidence_receipt_hashes),
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class FleetQualificationLedger:
    """Manages and projects military fleet qualification states without mutating core airspace objects."""

    RANK_THRESHOLDS = [
        (1000, "Fleet Admiral"),
        (500, "Commander"),
        (250, "Lieutenant Commander"),
        (100, "Lieutenant"),
        (0, "Flight Officer"),
    ]

    def __init__(self):
        self._records: Dict[str, QualificationRecord] = {}

    def issue_qualification(
        self,
        station_id: str,
        agent_id: str,
        qualifications: List[str],
        xp_earned: int,
        evidence_receipt_hashes: Optional[List[str]] = None,
    ) -> QualificationRecord:
        """Issue a new qualification record for an agent based on verified evidence."""
        receipts = evidence_receipt_hashes or []

        # Derive rank title from total XP
        rank_title = "Flight Officer"
        for threshold, title in self.RANK_THRESHOLDS:
            if xp_earned >= threshold:
                rank_title = title
                break

        record_id = f"qual-{agent_id}-{time.time_ns()}"
        record = QualificationRecord(
            record_id=record_id,
            station_id=station_id,
            agent_id=agent_id,
            rank_title=rank_title,
            qualifications=qualifications,
            xp_earned=xp_earned,
            evidence_receipt_hashes=receipts,
        )
        record.record_hash = record.compute_hash()

        self._records[record_id] = record
        return record

    def get_agent_summary(self, agent_id: str) -> Dict[str, Any]:
        """Aggregate qualification history for an agent."""
        agent_records = [r for r in self._records.values() if r.agent_id == agent_id]
        if not agent_records:
            return {
                "agent_id": agent_id,
                "rank_title": "Unranked",
                "total_xp": 0,
                "qualifications": [],
                "record_count": 0,
            }

        total_xp = sum(r.xp_earned for r in agent_records)
        all_quals = sorted(list({q for r in agent_records for q in r.qualifications}))

        rank_title = "Flight Officer"
        for threshold, title in self.RANK_THRESHOLDS:
            if total_xp >= threshold:
                rank_title = title
                break

        return {
            "agent_id": agent_id,
            "rank_title": rank_title,
            "total_xp": total_xp,
            "qualifications": all_quals,
            "record_count": len(agent_records),
        }
