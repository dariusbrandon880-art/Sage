"""Evidence-closure helpers for capability promotion decisions."""

from pathlib import Path
from typing import List
from pydantic import BaseModel
from sage.capability_registry import SAGECapability


class EvidenceClosure(BaseModel):
    capability_id: str
    missing_evidence: List[str] = []
    missing_tests: List[str] = []

    @property
    def closed(self) -> bool:
        return not self.missing_evidence and not self.missing_tests


def assess_evidence_closure(capability: SAGECapability, root: str = ".") -> EvidenceClosure:
    """Check whether declared evidence and tests actually exist; never mutates state."""
    base = Path(root)
    missing_evidence = [p for p in capability.evidence_references if not (base / p).exists()]
    missing_tests = [p for p in capability.test_references if not (base / p).exists()]
    return EvidenceClosure(
        capability_id=capability.capability_id,
        missing_evidence=missing_evidence,
        missing_tests=missing_tests,
    )
