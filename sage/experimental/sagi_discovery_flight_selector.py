"""Governed bridge from discovery intelligence to SAGI flight portfolios.

This module selects experiments; it does not authorize, execute, promote, or
qualify them. External research is candidate intelligence only. Canonical SAGE
state and observed flight evidence remain authoritative.

Flight slots are anonymous execution containers. Mission/capability identity
belongs to the candidate mission, never to F1-F5.
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
    capability_surface: str = ""


@dataclass(frozen=True)
class FlightSelectionProposal:
    candidates: tuple[DiscoveryCandidate, ...]
    frontier_digest: str
    selection_digest: str


class SAGIDiscoveryFlightSelector:
    """Select a distinct capability portfolio for reusable flight slots."""

    @staticmethod
    def _validate_candidate(candidate: DiscoveryCandidate) -> None:
        if not isinstance(candidate.role, FlightRole):
            raise ValueError("candidate role must be a governed FlightRole")
        if not candidate.candidate_id.strip() or not candidate.description.strip():
            raise ValueError("candidate identity and description are required")
        if not candidate.provenance_ref.strip():
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
            "\x1f".join(
                (
                    c.role.value,
                    c.candidate_id.strip(),
                    c.description.strip(),
                    f"{c.consequentiality:.17g}",
                    f"{c.information_gain:.17g}",
                    f"{c.falsification_value:.17g}",
                    f"{c.safety:.17g}",
                    f"{c.evidence_gap:.17g}",
                    c.provenance_ref.strip(),
                    c.capability_surface.strip(),
                )
            )
            for c in candidates
        )
        return hashlib.sha256(f"{frontier_digest.strip()}|{material}".encode("utf-8")).hexdigest()

    def select(
        self,
        candidates: tuple[DiscoveryCandidate, ...],
        *,
        frontier_digest: str,
        selection_digest: str | None = None,
        portfolio_size: int = 5,
    ) -> FlightSelectionProposal:
        """Select the highest-value safe, distinct capability missions.

        No semantic role is required or mapped to a flight slot. Roles remain
        discovery metadata only. When capability surfaces are supplied, selection
        prefers distinct surfaces so a wave does not recycle one frontier.
        """
        if not frontier_digest.strip():
            raise ValueError("selection requires canonical frontier digest")
        if not candidates:
            raise ValueError("selection requires discovery candidates")
        if portfolio_size < 1:
            raise ValueError("portfolio size must be positive")

        seen: set[str] = set()
        for candidate in candidates:
            self._validate_candidate(candidate)
            if candidate.candidate_id in seen:
                raise ValueError("candidate IDs must be unique")
            seen.add(candidate.candidate_id)

        safe = [c for c in candidates if c.safety > 0.0]
        if len(safe) < portfolio_size:
            raise ValueError("not enough safe candidates for requested portfolio")

        ranked = sorted(safe, key=self._score, reverse=True)
        selected: list[DiscoveryCandidate] = []
        used_surfaces: set[str] = set()

        # First pass maximizes capability-surface diversity. Empty surfaces remain
        # valid legacy candidates and are treated as unknown rather than a domain.
        for candidate in ranked:
            surface = candidate.capability_surface.strip()
            if surface and surface in used_surfaces:
                continue
            selected.append(candidate)
            if surface:
                used_surfaces.add(surface)
            if len(selected) == portfolio_size:
                break

        # If fewer distinct surfaces exist, fill remaining slots by value. This is
        # a portfolio constraint, not a semantic assignment to F1-F5.
        if len(selected) < portfolio_size:
            selected_ids = {c.candidate_id for c in selected}
            for candidate in ranked:
                if candidate.candidate_id in selected_ids:
                    continue
                selected.append(candidate)
                if len(selected) == portfolio_size:
                    break

        selected_tuple = tuple(selected)
        derived_digest = self._digest(selected_tuple, frontier_digest)
        if selection_digest is not None and selection_digest != derived_digest:
            raise ValueError("selection digest does not match selected portfolio")

        return FlightSelectionProposal(
            candidates=selected_tuple,
            frontier_digest=frontier_digest.strip(),
            selection_digest=derived_digest,
        )
