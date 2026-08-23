import time

import pytest

from sage.experimental.coherent_frontier import StageStatus
from sage.experimental.parallel_frontier import ParallelFrontierExecutor, ParallelStage


def test_independent_stages_run_concurrently():
    def work(value):
        def run():
            time.sleep(0.05)
            return value
        return run

    receipt = ParallelFrontierExecutor(
        "parallel",
        [ParallelStage("a", work("a")), ParallelStage("b", work("b"))],
        max_workers=2,
    ).execute()

    assert receipt.verdict is StageStatus.PASS
    assert receipt.completed_stage_ids == ("a", "b")


def test_failed_stage_blocks_only_dependents():
    def fail():
        raise RuntimeError("boom")

    receipt = ParallelFrontierExecutor(
        "failure-isolation",
        [
            ParallelStage("bad", fail),
            ParallelStage("independent", lambda: "ok"),
            ParallelStage("dependent", lambda: "never", depends_on=("bad",)),
        ],
    ).execute()

    assert receipt.verdict is StageStatus.FAILED
    states = {o.stage_id: o.status for o in receipt.observations}
    assert states == {
        "bad": StageStatus.FAILED,
        "independent": StageStatus.PASS,
        "dependent": StageStatus.BLOCKED,
    }


def test_invalid_graph_fails_closed():
    with pytest.raises(ValueError):
        ParallelFrontierExecutor(
            "cycle",
            [ParallelStage("a", lambda: None, depends_on=("b",)), ParallelStage("b", lambda: None, depends_on=("a",))],
        )
