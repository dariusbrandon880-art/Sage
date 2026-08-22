"""Governed bridge from discovery intelligence to SAGI flight portfolios.

This module selects experiments; it does not authorize, execute, promote, or
qualify them. External research is candidate intelligence only. Canonical SAGE
state and observed flight evidence remain authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib


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

    @staticmethod
    def _validate_candidate(candidate: DiscoveryCandidate) -> None:
        if not candidate.candidate_id or not candidate.description:
            raise ValueError("candidate identity and description are required")
        if not candidate.provenance_ref:
            raise ValueError("candidate provenance is required")
        for value in (
            candidate.consequentiality,
            candidate.information_gain,
            candidate.falsification_value,
            candidate.safety,
            candidate.evidence_gap,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("candidate scores must be normalized to [0, 1]")

    @staticmethod
    def _score(candidate: DiscoveryCandidate) -> tuple[float, float, str]:
        # Information value dominates; safety gates selection rather than becoming
        # a reward for risky candidates. Candidate ID is a deterministic tie-break.
        value = (
            0.35 * candidate.consequentiality
            + 0.30 * candidate.information_gain
            + 0.20 * candidate.falsification_value
            + 0.15 * candidate.evidence_gap
        )
        return value, candidate.safety, candidate.candidate_id

    @staticmethod
    def _digest(
        candidates: tuple[DiscoveryCandidate, ...], frontier_digest: str
    ) -> str:
        material = "|".join(
            f"{c.role.value}:{c.candidate_id}:{c.provenance_ref}"
            for c in candidates
        )
        return hashlib.sha256(f"{frontier_digest}|{material}".encode()).hexdigest()

    def select(
        self,
        candidates: tuple[DiscoveryCandidate, ...],
        *,
        frontier_digest: str,
        selection_digest: str | None = None,
    ) -> FlightSelectionProposal:
        if not frontier_digest:
            raise ValueError("selection requires canonical frontier digest")
        if not candidates:
            raise ValueError("selection requires discovery candidates")

        seen: set[str] = set()
        for candidate in candidates:
            self._validate_candidate(candidate)
            if candidate.candidate_id in seen:
                raise ValueError("candidate IDs must be unique")
            seen.add(candidate.candidate_id)

        selected: list[DiscoveryCandidate] = []
        for role in self.REQUIRED_ROLES:
            pool = [
                c for c in candidates
                if c.role is role and c.safety > 0.0
            ]
            if not pool:
                raise ValueError(f"no safe candidate for required role: {role.value}")
            selected.append(max(pool, key=self._score))

        selected_tuple = tuple(selected)
        derived_digest = self._digest(selected_tuple, frontier_digest)
        if selection_digest is not None and selection_digest != derived_digest:
            raise ValueError("selection digest does not match selected portfolio")

        return FlightSelectionProposal(
            candidates=selected_tuple,
            frontier_digest=frontier_digest,
            selection_digest=derived_digest,
        )
