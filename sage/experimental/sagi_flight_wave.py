"""Materialize a selected SAGI five-flight portfolio into a 20-cell wave.

This is a pure planning projection. It does not execute, authorize, persist,
or qualify any flight. Execution remains behind the existing governed runner.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from sage.experimental.sagi_discovery_flight_selector import FlightSelectionProposal


class WaveCellKind(str, Enum):
    RECOVERY = "004"
    REUSE = "005"
    RETENTION_REGRESSION = "006"
    COMPOUND = "007"


@dataclass(frozen=True)
class SAGIWaveCell:
    campaign_id: str
    candidate_id: str
    role: str
    flight_cell: WaveCellKind
    frontier_digest: str
    provenance_ref: str


@dataclass(frozen=True)
class SAGIWavePlan:
    selection_digest: str
    cells: tuple[SAGIWaveCell, ...]

    @property
    def expected_cell_count(self) -> int:
        return len(self.cells)


def materialize_wave(proposal: FlightSelectionProposal) -> SAGIWavePlan:
    """Turn five selected experiments into five campaigns x four cells."""
    if len(proposal.candidates) != 5:
        raise ValueError("SAGI wave requires exactly five selected flights")

    cells: list[SAGIWaveCell] = []
    for campaign_number, candidate in enumerate(proposal.candidates, start=1):
        campaign_id = f"{campaign_number:02d}"
        for cell_kind in WaveCellKind:
            cells.append(
                SAGIWaveCell(
                    campaign_id=campaign_id,
                    candidate_id=candidate.candidate_id,
                    role=candidate.role.value,
                    flight_cell=cell_kind,
                    frontier_digest=proposal.frontier_digest,
                    provenance_ref=candidate.provenance_ref,
                )
            )

    return SAGIWavePlan(proposal.selection_digest, tuple(cells))
