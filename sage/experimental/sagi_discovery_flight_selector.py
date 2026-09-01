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
        # Bind the complete selected payload, including every score that can affect
        # selection. Identity-only hashing would allow semantic candidate tampering
        # without changing the recorded selection digest.
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
    ) -> FlightSelectionProposal:
        if not frontier_digest.strip():
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
            frontier_digest=frontier_digest.strip(),
            selection_digest=derived_digest,
        )

    @classmethod
    def generate_broad_surface_candidates(cls, provenance_ref: str = "sage/discovery/broad_surface") -> tuple[DiscoveryCandidate, ...]:
        """Generate candidate missions spanning Observatory, Sports, SAGI, C2, and Airspace.

        Slots F1-F5 remain anonymous execution containers; candidates express semantic
        capabilities across the full SAGE surface without permanent slot binding.
        """
        return (
            DiscoveryCandidate(
                candidate_id="observatory-hud-health",
                description="Observatory HUD state reconciliation and command console endpoint health audit",
                role=FlightRole.CONSEQUENT_FRONTIER,
                consequentiality=0.90,
                information_gain=0.85,
                falsification_value=0.80,
                safety=0.95,
                evidence_gap=0.70,
                provenance_ref=provenance_ref,
            ),
            DiscoveryCandidate(
                candidate_id="sports-shadow-beta",
                description="Sports quantitative shadow beta temporal firewall and signal attribution check",
                role=FlightRole.INFORMATION_GAIN,
                consequentiality=0.85,
                information_gain=0.92,
                falsification_value=0.88,
                safety=0.90,
                evidence_gap=0.75,
                provenance_ref=provenance_ref,
            ),
            DiscoveryCandidate(
                candidate_id="sagi-brain-falsification",
                description="SAGI brain state integrity verification and CRPL F3 mutation bound isolation",
                role=FlightRole.FALSIFICATION,
                consequentiality=0.95,
                information_gain=0.90,
                falsification_value=0.96,
                safety=0.88,
                evidence_gap=0.80,
                provenance_ref=provenance_ref,
            ),
            DiscoveryCandidate(
                candidate_id="c2-governance-hardening",
                description="C2 transition authority engine state-digest verification and anti-replay audit",
                role=FlightRole.RECOVERY_REGRESSION,
                consequentiality=0.88,
                information_gain=0.82,
                falsification_value=0.85,
                safety=0.92,
                evidence_gap=0.65,
                provenance_ref=provenance_ref,
            ),
            DiscoveryCandidate(
                candidate_id="airspace-fleet-evolution",
                description="Airspace fleet evolution cross-station nameplate and organism growth verification",
                role=FlightRole.INDEPENDENT_TRANSFER,
                consequentiality=0.82,
                information_gain=0.88,
                falsification_value=0.78,
                safety=0.94,
                evidence_gap=0.72,
                provenance_ref=provenance_ref,
            ),
        )
