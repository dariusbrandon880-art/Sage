"""Governed supervisor for parallel SAGE frontier campaigns.

The supervisor does not grant authority or qualify capability. It makes
parallel execution complete/observable: every expected cell must terminate
with an explicit verdict or evidence-backed blocked state before a campaign
can be considered complete.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping


class CellStatus(str, Enum):
    PASS = "PASS"
    HOLD = "HOLD"
    NEGATIVE_RESULT = "NEGATIVE_RESULT"
    BLOCKED_WITH_EVIDENCE = "BLOCKED_WITH_EVIDENCE"
    PENDING = "PENDING"


@dataclass(frozen=True)
class FlightCell:
    cell_id: str
    mission: str


@dataclass(frozen=True)
class CellObservation:
    cell_id: str
    status: CellStatus
    evidence_ref: str | None = None
    shared_failure_key: str | None = None


@dataclass(frozen=True)
class CampaignVerdict:
    complete: bool
    status: CellStatus
    missing_cells: tuple[str, ...] = ()
    shared_failure_keys: tuple[str, ...] = ()
    observations: tuple[CellObservation, ...] = ()


@dataclass
class ParallelFrontierSupervisor:
    """Enforce campaign completeness across independently executed cells."""

    expected_cells: tuple[FlightCell, ...]
    _observations: dict[str, CellObservation] = field(default_factory=dict)

    def record(self, observation: CellObservation) -> None:
        expected = {cell.cell_id for cell in self.expected_cells}
        if observation.cell_id not in expected:
            raise ValueError(f"unexpected flight cell: {observation.cell_id}")
        if observation.status is not CellStatus.PENDING and not observation.evidence_ref:
            raise ValueError("non-pending cell observations require evidence_ref")
        self._observations[observation.cell_id] = observation

    def record_many(self, observations: Iterable[CellObservation]) -> None:
        for observation in observations:
            self.record(observation)

    def evaluate(self) -> CampaignVerdict:
        expected = {cell.cell_id for cell in self.expected_cells}
        missing = tuple(sorted(expected - self._observations.keys()))
        observations = tuple(
            self._observations[cell.cell_id]
            for cell in self.expected_cells
            if cell.cell_id in self._observations
        )
        if missing:
            return CampaignVerdict(
                complete=False,
                status=CellStatus.HOLD,
                missing_cells=missing,
                observations=observations,
            )

        shared_failures = tuple(
            sorted(
                {
                    observation.shared_failure_key
                    for observation in observations
                    if observation.shared_failure_key
                }
            )
        )
        if shared_failures:
            return CampaignVerdict(
                complete=True,
                status=CellStatus.BLOCKED_WITH_EVIDENCE,
                shared_failure_keys=shared_failures,
                observations=observations,
            )

        statuses = {observation.status for observation in observations}
        if CellStatus.NEGATIVE_RESULT in statuses:
            status = CellStatus.NEGATIVE_RESULT
        elif CellStatus.HOLD in statuses:
            status = CellStatus.HOLD
        else:
            status = CellStatus.PASS
        return CampaignVerdict(
            complete=True,
            status=status,
            observations=observations,
        )

    @property
    def complete(self) -> bool:
        return self.evaluate().complete
