"""Evidence-bounded Super Search candidate intake for Frontier Tree."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DiscoveryKind(str, Enum):
    KNOWN = "KNOWN"
    TRANSFERRED = "TRANSFERRED"
    HYPOTHESIZED = "HYPOTHESIZED"


@dataclass(frozen=True)
class DiscoveryCandidate:
    candidate_id: str
    claim: str
    kind: DiscoveryKind
    provenance: tuple[str, ...]
    challenge_status: str

    def admissible(self) -> bool:
        return bool(self.provenance) and self.challenge_status in {"CHALLENGED", "BOUNDED"}


def admit(candidate: DiscoveryCandidate) -> DiscoveryCandidate:
    if not candidate.admissible():
        raise ValueError("discovery candidate lacks governed provenance or challenge boundary")
    return candidate
