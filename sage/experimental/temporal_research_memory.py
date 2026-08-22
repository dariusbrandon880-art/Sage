"""Versioned research snapshots with deterministic temporal comparison."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from typing import Mapping, Any

@dataclass(frozen=True)
class ResearchSnapshot:
    snapshot_id: str
    observed_at: str
    facts: Mapping[str, Any]
    evidence_refs: tuple[str, ...]
    digest: str

class TemporalResearchMemory:
    def __init__(self) -> None:
        self._snapshots: dict[str, ResearchSnapshot] = {}
    def record(self, snapshot_id: str, observed_at: str, facts: Mapping[str, Any], evidence_refs: tuple[str,...]) -> ResearchSnapshot:
        if snapshot_id in self._snapshots: raise ValueError("DUPLICATE_SNAPSHOT")
        payload=json.dumps(dict(facts),sort_keys=True,separators=(",",":"),default=str)
        digest=hashlib.sha256(payload.encode()).hexdigest()
        snap=ResearchSnapshot(snapshot_id,observed_at,dict(facts),tuple(evidence_refs),digest)
        self._snapshots[snapshot_id]=snap
        return snap
    def compare(self, earlier: str, later: str) -> dict[str, tuple[Any,Any]]:
        a,b=self._snapshots[earlier],self._snapshots[later]
        keys=set(a.facts)|set(b.facts)
        return {k:(a.facts.get(k),b.facts.get(k)) for k in sorted(keys) if a.facts.get(k)!=b.facts.get(k)}
    def get(self, snapshot_id: str) -> ResearchSnapshot: return self._snapshots[snapshot_id]
