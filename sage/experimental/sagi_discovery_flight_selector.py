"""Governed bridge from discovery intelligence to SAGI flight portfolios.

This module selects experiments; it does not authorize, execute, promote, or
qualify them. External research is candidate evidence only. Canonical SAGE
state and observed flight evidence remain authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FlightRole(str, Enum):
    CONSEQUENT_FRONTIER = "CONSEQUENT_FRONTIER"
    INFORMATION_GAIN = "INFORMATION_GAIN"
    FALSIFICATION = "FALSIFICATION"
    RECOVERY_REGRESSION = "RECOVERY_REGRESSION"
    INDEPENDENT_TRANSFER = "INDEPENDENT_TRANSFER"


@dataclass(frozen=True)
class DiscoveryCandidate:
    candidate_id: str
    description: str
    role: FlightRole
    consequentiality: float
    information_gain: float
    falsification_value: float
    safety: float
    evidence_gap: float
    provenance_ref: str


@dataclass(frozen=True)
class FlightSelectionProposal:
    candidates: tuple[DiscoveryCandidate, ...]
    frontier_digest: str
    selection_digest: str


class SAGIDiscoveryFlightSelector:
    """Select a diversified five-flight portfolio from governed candidates."""

    REQUIRED_ROLES = (
        FlightRole.CONSEQUENT_FRONTIER,
        FlightRole.INFORMATION_GAIN,
        FlightRole.FALSIFICATION,
        FlightRole.RECOVERY_REGRESSION,
        FlightRole.INDEPENDENT_TRANSFER,
    )

    def select(
        self,
        candidates: tuple[DiscoveryCandidate, ...],
        *,
        frontier_digest: str,
        selection_digest: str,
    ) -> FlightSelectionProposal:
        if not frontier_digest or not selection_digest:
            raise ValueError("selection requires canonical frontier and digest")
        selected: list[DiscoveryCandidate] = []
        for role in self.REQUIRED_ROLES:
            pool = [c for c in candidates if c.role is role and c.safety > 0]
            if not pool:
                raise ValueError(f"no safe candidate for required role: {role.value}")
            selected.append(
                max(
                    pool,
                    key=lambda c: (
                        c.consequentiality
                        + c.information_gain
                        + c.falsification_value
                        + c.evidence_gap
                    )
                    * c.safety,
                )
            )
        return FlightSelectionProposal(tuple(selected), frontier_digest, selection_digest)
