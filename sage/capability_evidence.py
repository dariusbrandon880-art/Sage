"""Evidence-closure helpers for capability promotion decisions."""

from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from sage.capability_registry import SAGECapability


class EvidenceClosure(BaseModel):
    capability_id: str
    missing_evidence: List[str] = Field(default_factory=list)
    missing_tests: List[str] = Field(default_factory=list)

    @property
    def closed(self) -> bool:
        return not self.missing_evidence and not self.missing_tests


def assess_evidence_closure(capability: SAGECapability, root: str = ".") -> EvidenceClosure:
    """Check whether declared evidence and tests actually exist; never mutates state."""
    base = Path(root)
    return EvidenceClosure(
        capability_id=capability.capability_id,
        missing_evidence=[p for p in capability.evidence_references if not (base / p).exists()],
        missing_tests=[p for p in capability.test_references if not (base / p).exists()],
    )
