"""Governed execution of one coherent consequential frontier.

Large Build is intentionally *batching*, not skipping: every required stage is
still executed, observed, and recorded, but causally connected stages travel as
one campaign instead of forcing an artificial conversational stop after each
substep.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Sequence


class StageStatus(str, Enum):
    """Observed outcome for one frontier stage."""

    PENDING = "PENDING"
    PASS = "PASS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class FrontierStage:
    """One consequential substep inside a larger authorized frontier."""

    stage_id: str
    execute: Callable[[], Any]
    depends_on: tuple[str, ...] = ()
    required: bool = True


@dataclass(frozen=True)
class StageObservation:
    """Durable in-memory observation of an executed or blocked stage."""

    stage_id: str
    status: StageStatus
    output: Any = None
    error: Optional[str] = None


@dataclass(frozen=True)
class FrontierReceipt:
    """Campaign-level evidence; never a capability qualification."""

    frontier_id: str
    observations: tuple[StageObservation, ...]
    completed_stage_ids: tuple[str, ...]
    failed_stage_ids: tuple[str, ...]
    blocked_stage_ids: tuple[str, ...]
    verdict: StageStatus

    @property
    def evidence_complete(self) -> bool:
        return all(o.status == StageStatus.PASS for o in self.observations)


class CoherentFrontierExecutor:
    """Execute all connected authorized stages in one governed campaign.

    The executor preserves stage-level gates while eliminating artificial
    orchestration stops. Independent stages can still run after another stage
    fails; dependent stages are fail-closed as BLOCKED. No stage is silently
    skipped and no failure is converted into success.
    """

    def __init__(self, frontier_id: str, stages: Sequence[FrontierStage]):
        if not frontier_id:
            raise ValueError("frontier_id is required")
        self.frontier_id = frontier_id
        self.stages = tuple(stages)
        self._validate_graph()

    def _validate_graph(self) -> None:
        ids = [stage.stage_id for stage in self.stages]
        if len(ids) != len(set(ids)):
            raise ValueError("frontier stage IDs must be unique")
        known = set(ids)
        for stage in self.stages:
            if stage.stage_id in stage.depends_on:
                raise ValueError(f"stage '{stage.stage_id}' cannot depend on itself")
            unknown = set(stage.depends_on) - known
            if unknown:
                raise ValueError(
                    f"stage '{stage.stage_id}' has unknown dependencies: {sorted(unknown)}"
                )
        remaining = {stage.stage_id: set(stage.depends_on) for stage in self.stages}
        resolved: set[str] = set()
        while remaining:
            ready = [stage_id for stage_id, deps in remaining.items() if deps <= resolved]
            if not ready:
                raise ValueError("frontier dependency graph contains a cycle")
            for stage_id in ready:
                resolved.add(stage_id)
                del remaining[stage_id]

    def execute(self) -> FrontierReceipt:
        """Run the whole authorized frontier and return one campaign receipt."""
        observations: Dict[str, StageObservation] = {}

        for stage in self.stages:
            blocked_by = [
                dep for dep in stage.depends_on
                if observations.get(dep, StageObservation(dep, StageStatus.BLOCKED)).status
                != StageStatus.PASS
            ]
            if blocked_by:
                observations[stage.stage_id] = StageObservation(
                    stage_id=stage.stage_id,
                    status=StageStatus.BLOCKED,
                    error=f"blocked by failed/incomplete dependency: {blocked_by}",
                )
                continue

            try:
                output = stage.execute()
            except Exception as exc:  # noqa: BLE001 - governance boundary is fail-closed
                observations[stage.stage_id] = StageObservation(
                    stage_id=stage.stage_id,
                    status=StageStatus.FAILED,
                    error=f"{type(exc).__name__}: {exc}",
                )
            else:
                observations[stage.stage_id] = StageObservation(
                    stage_id=stage.stage_id,
                    status=StageStatus.PASS,
                    output=output,
                )

        ordered = tuple(observations[stage.stage_id] for stage in self.stages)
        completed = tuple(o.stage_id for o in ordered if o.status == StageStatus.PASS)
        failed = tuple(o.stage_id for o in ordered if o.status == StageStatus.FAILED)
        blocked = tuple(o.stage_id for o in ordered if o.status == StageStatus.BLOCKED)
        required_failures = any(
            stage.required and observations[stage.stage_id].status != StageStatus.PASS
            for stage in self.stages
        )
        verdict = StageStatus.FAILED if required_failures else StageStatus.PASS
        return FrontierReceipt(
            frontier_id=self.frontier_id,
            observations=ordered,
            completed_stage_ids=completed,
            failed_stage_ids=failed,
            blocked_stage_ids=blocked,
            verdict=verdict,
        )
