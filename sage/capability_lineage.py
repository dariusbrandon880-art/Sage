"""Semantic lineage records for reconciling historical capability projections."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CapabilityLineage(BaseModel):
    """Evidence-bearing lineage from a historical concept to current state."""

    historical_concept: str = Field(..., min_length=1)
    current_capability_id: Optional[str] = None
    implementation_paths: List[str] = Field(default_factory=list)
    evidence_paths: List[str] = Field(default_factory=list)
    status: str = Field(
        ...,
        description="One of VALIDATED, ACTIVE_BUILD, READY_FRONTIER, RESEARCH_CANDIDATE, DEPENDENCY, NEGATIVE_CLOSED, STALE_CONFLICTING.",
    )
    remaining_gap: Optional[str] = None


class CapabilityLineageIndex:
    """Deterministic, non-authoritative lineage index used during reconciliation."""

    def __init__(self, records: Optional[List[CapabilityLineage]] = None) -> None:
        self.records = list(records or [])

    def add(self, record: CapabilityLineage) -> None:
        self.records.append(record)

    def for_capability(self, capability_id: str) -> List[CapabilityLineage]:
        return [r for r in self.records if r.current_capability_id == capability_id]

    def unresolved(self) -> List[CapabilityLineage]:
        return [r for r in self.records if r.status != "VALIDATED"]

    def duplicate_current_ids(self) -> List[str]:
        counts = {}
        for record in self.records:
            if record.current_capability_id:
                counts[record.current_capability_id] = counts.get(record.current_capability_id, 0) + 1
        return sorted(cap_id for cap_id, count in counts.items() if count > 1)
