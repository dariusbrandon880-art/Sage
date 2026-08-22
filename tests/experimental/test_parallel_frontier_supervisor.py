import pytest

from sage.experimental.parallel_frontier_supervisor import (
    CellObservation,
    CellStatus,
    FlightCell,
    ParallelFrontierSupervisor,
)


CELLS = tuple(FlightCell(str(i), mission) for i, mission in enumerate(
    ("recovery", "reuse", "retention", "compound"), start=4
))


def test_partial_campaign_is_hold_and_names_missing_cells():
    supervisor = ParallelFrontierSupervisor(CELLS)
    supervisor.record(CellObservation("4", CellStatus.PASS, "e4"))
    result = supervisor.evaluate()
    assert result.complete is False
    assert result.status is CellStatus.HOLD
    assert result.missing_cells == ("5", "6", "7")


def test_every_terminal_cell_requires_evidence():
    supervisor = ParallelFrontierSupervisor(CELLS)
    with pytest.raises(ValueError):
        supervisor.record(CellObservation("4", CellStatus.PASS))


def test_shared_failure_collapses_to_one_repair_frontier():
    supervisor = ParallelFrontierSupervisor(CELLS)
    supervisor.record_many(
        CellObservation(str(i), CellStatus.BLOCKED_WITH_EVIDENCE, f"e{i}", "launcher-import")
        for i in range(4, 8)
    )
    result = supervisor.evaluate()
    assert result.complete is True
    assert result.status is CellStatus.BLOCKED_WITH_EVIDENCE
    assert result.shared_failure_keys == ("launcher-import",)


def test_complete_campaign_uses_worst_epistemic_outcome():
    supervisor = ParallelFrontierSupervisor(CELLS)
    supervisor.record_many(
        [
            CellObservation("4", CellStatus.PASS, "e4"),
            CellObservation("5", CellStatus.PASS, "e5"),
            CellObservation("6", CellStatus.HOLD, "e6"),
            CellObservation("7", CellStatus.PASS, "e7"),
        ]
    )
    assert supervisor.evaluate().status is CellStatus.HOLD


def test_negative_result_dominates_hold_for_complete_campaign():
    supervisor = ParallelFrontierSupervisor(CELLS)
    supervisor.record_many(
        [
            CellObservation("4", CellStatus.PASS, "e4"),
            CellObservation("5", CellStatus.NEGATIVE_RESULT, "e5"),
            CellObservation("6", CellStatus.HOLD, "e6"),
            CellObservation("7", CellStatus.PASS, "e7"),
        ]
    )
    assert supervisor.evaluate().status is CellStatus.NEGATIVE_RESULT
