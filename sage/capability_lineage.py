"""Read-only capability/evidence lineage projection.

This projection does not create a second capability registry and never mutates
canonical state. It evaluates the existing operational capability registry
against the repository's current implementation, evidence, and test surfaces.
"""

from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, Field

from sage.capability_registry import SAGECapability, SAGEOperationalCapabilityRegistry


Lifecycle = Literal[
    "VALIDATED",
    "STALE_EVIDENCE",
    "STALE_TEST",
    "UNVERIFIED",
    "IMPLEMENTATION_GAP",
]


class CapabilityLineageRecord(BaseModel):
    capability_id: str
    name: str
    implementation_status: str
    declared_validation_status: str
    effective_lifecycle: Lifecycle
    missing_evidence: List[str] = Field(default_factory=list)
    missing_tests: List[str] = Field(default_factory=list)
    evidence_references: List[str] = Field(default_factory=list)
    test_references: List[str] = Field(default_factory=list)


class CapabilityLineageProjection(BaseModel):
    """Deterministic, zero-storage view over the existing registry."""

    capabilities: List[CapabilityLineageRecord]

    @property
    def stale_count(self) -> int:
        return sum(r.effective_lifecycle != "VALIDATED" for r in self.capabilities)


def _status(capability: SAGECapability, missing_evidence: List[str], missing_tests: List[str]) -> Lifecycle:
    if capability.implementation_status.upper() != "IMPLEMENTED":
        return "IMPLEMENTATION_GAP"
    if capability.validation_status.upper() != "VALIDATED":
        return "UNVERIFIED"
    if missing_evidence:
        return "STALE_EVIDENCE"
    if missing_tests:
        return "STALE_TEST"
    return "VALIDATED"


def project_capability_lineage(
    registry: SAGEOperationalCapabilityRegistry,
    root: str | Path = ".",
) -> CapabilityLineageProjection:
    """Project current repository freshness without changing registry state."""
    base = Path(root)
    records: List[CapabilityLineageRecord] = []
    for capability in registry.list_capabilities():
        missing_evidence = [
            ref for ref in capability.evidence_references if not (base / ref).is_file()
        ]
        missing_tests = [
            ref for ref in capability.test_references if not (base / ref).is_file()
        ]
        records.append(
            CapabilityLineageRecord(
                capability_id=capability.capability_id,
                name=capability.name,
                implementation_status=capability.implementation_status,
                declared_validation_status=capability.validation_status,
                effective_lifecycle=_status(capability, missing_evidence, missing_tests),
                missing_evidence=missing_evidence,
                missing_tests=missing_tests,
                evidence_references=list(capability.evidence_references),
                test_references=list(capability.test_references),
            )
        )
    return CapabilityLineageProjection(capabilities=records)


def project_from_path(
    registry_path: str = "evidence_capture/operational_capability_registry.json",
    root: str | Path = ".",
) -> CapabilityLineageProjection:
    """Convenience entry point using the existing registry storage."""
    return project_capability_lineage(SAGEOperationalCapabilityRegistry(registry_path), root)
