"""Adversarial tests for the governed Large-Build campaign primitive."""

import pytest

from sage.experimental.coherent_frontier import (
    CoherentFrontierExecutor,
    FrontierStage,
    StageStatus,
)


def test_executes_connected_stages_in_one_campaign_and_keeps_observations():
    events = []
    frontier = CoherentFrontierExecutor(
        "frontier-001",
        [
            FrontierStage("recon", lambda: events.append("recon") or "r"),
            FrontierStage("build", lambda: events.append("build") or "b", ("recon",)),
            FrontierStage("test", lambda: events.append("test") or "t", ("build",)),
            FrontierStage("independent", lambda: events.append("independent") or "i"),
        ],
    )

    receipt = frontier.execute()

    assert events == ["recon", "build", "test", "independent"]
    assert receipt.verdict is StageStatus.PASS
    assert receipt.completed_stage_ids == ("recon", "build", "test", "independent")
    assert receipt.evidence_complete


def test_failure_does_not_stop_independent_work_but_blocks_dependents():
    events = []
    frontier = CoherentFrontierExecutor(
        "frontier-002",
        [
            FrontierStage("recon", lambda: events.append("recon") or "r"),
            FrontierStage("broken_build", lambda: (_ for _ in ()).throw(RuntimeError("boom")), ("recon",)),
            FrontierStage("dependent_test", lambda: events.append("dependent") or "t", ("broken_build",)),
            FrontierStage("independent_verify", lambda: events.append("verify") or "v"),
        ],
    )

    receipt = frontier.execute()

    assert events == ["recon", "verify"]
    assert receipt.verdict is StageStatus.FAILED
    assert receipt.failed_stage_ids == ("broken_build",)
    assert receipt.blocked_stage_ids == ("dependent_test",)
    assert receipt.completed_stage_ids == ("recon", "independent_verify")


def test_rejects_duplicate_or_cyclic_frontiers():
    with pytest.raises(ValueError, match="unique"):
        CoherentFrontierExecutor(
            "dup",
            [FrontierStage("x", lambda: None), FrontierStage("x", lambda: None)],
        )

    with pytest.raises(ValueError, match="cycle"):
        CoherentFrontierExecutor(
            "cycle",
            [
                FrontierStage("a", lambda: None, ("b",)),
                FrontierStage("b", lambda: None, ("a",)),
            ],
        )


def test_never_turns_exception_into_success():
    frontier = CoherentFrontierExecutor(
        "frontier-003",
        [FrontierStage("danger", lambda: 1 / 0)],
    )

    receipt = frontier.execute()

    assert receipt.verdict is StageStatus.FAILED
    assert receipt.observations[0].status is StageStatus.FAILED
    assert "ZeroDivisionError" in receipt.observations[0].error
