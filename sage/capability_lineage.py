"""Read-only capability/evidence freshness projection."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry

Lifecycle = Literal["VALIDATED", "STALE_EVIDENCE", "STALE_TEST", "UNVERIFIED", "IMPLEMENTATION_GAP"]


class CapabilityLineageRecord(BaseModel):
    capability_id: str
    name: str
    effective_lifecycle: Lifecycle
    missing_evidence: list[str] = Field(default_factory=list)
    missing_tests: list[str] = Field(default_factory=list)


class CapabilityLineageProjection(BaseModel):
    capabilities: list[CapabilityLineageRecord]

    @property
    def stale_count(self) -> int:
        return sum(record.effective_lifecycle != "VALIDATED" for record in self.capabilities)


def _status(capability: SAGECapability, missing_evidence: list[str], missing_tests: list[str]) -> Lifecycle:
    if capability.implementation_status.upper() != "IMPLEMENTED":
        return "IMPLEMENTATION_GAP"
    if capability.validation_status.upper() != "VALIDATED":
        return "UNVERIFIED"
    if missing_evidence:
        return "STALE_EVIDENCE"
    if missing_tests:
        return "STALE_TEST"
    return "VALIDATED"


def project_capability_lineage(registry: SAGEOperationalCapabilityRegistry, root: str | Path = ".") -> CapabilityLineageProjection:
    base = Path(root)
    records = []
    for capability in registry.list_capabilities():
        missing_evidence = [ref for ref in capability.evidence_references if not (base / ref).is_file()]
        missing_tests = [ref for ref in capability.test_references if not (base / ref).is_file()]
        records.append(CapabilityLineageRecord(capability_id=capability.capability_id, name=capability.name, effective_lifecycle=_status(capability, missing_evidence, missing_tests), missing_evidence=missing_evidence, missing_tests=missing_tests))
    return CapabilityLineageProjection(capabilities=records)
