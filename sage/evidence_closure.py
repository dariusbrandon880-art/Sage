"""Read-only evidence/test closure for the operational capability registry."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sage.capability_registry import SAGEOperationalCapabilityRegistry


@dataclass(frozen=True)
class ClosureRecord:
    capability_id: str
    missing_evidence: tuple[str, ...]
    missing_tests: tuple[str, ...]

    @property
    def closed(self) -> bool:
        return not self.missing_evidence and not self.missing_tests


def check_evidence_closure(registry: SAGEOperationalCapabilityRegistry, root: str | Path = ".") -> tuple[ClosureRecord, ...]:
    base = Path(root)
    records = []
    for capability in registry.list_capabilities():
        missing_evidence = tuple(ref for ref in capability.evidence_references if not (base / ref).is_file())
        missing_tests = tuple(ref for ref in capability.test_references if not (base / ref).is_file())
        records.append(ClosureRecord(capability.capability_id, missing_evidence, missing_tests))
    return tuple(records)


def require_closed(records: tuple[ClosureRecord, ...]) -> None:
    if any(not record.closed for record in records):
        raise ValueError("EVIDENCE_CLOSURE_INCOMPLETE")
