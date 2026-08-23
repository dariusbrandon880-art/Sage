"""Parallel execution for one governed coherent frontier.

Independent stages run concurrently; dependency edges remain fail-closed.
This module adds scheduling velocity without adding authority or changing the
existing CoherentFrontierExecutor contract.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from sage.experimental.coherent_frontier import StageObservation, StageStatus


@dataclass(frozen=True)
class ParallelStage:
    stage_id: str
    execute: Callable[[], Any]
    depends_on: tuple[str, ...] = ()
    required: bool = True


@dataclass(frozen=True)
class ParallelFrontierReceipt:
    frontier_id: str
    observations: tuple[StageObservation, ...]
    completed_stage_ids: tuple[str, ...]
    failed_stage_ids: tuple[str, ...]
    blocked_stage_ids: tuple[str, ...]
    verdict: StageStatus

    @property
    def evidence_complete(self) -> bool:
        return all(o.status == StageStatus.PASS for o in self.observations)


class ParallelFrontierExecutor:
    """Run independent frontier stages concurrently while preserving gates."""

    def __init__(self, frontier_id: str, stages: Sequence[ParallelStage], max_workers: int = 5):
        if not frontier_id:
            raise ValueError("frontier_id is required")
        if max_workers < 1:
            raise ValueError("max_workers must be positive")
        self.frontier_id = frontier_id
        self.stages = tuple(stages)
        self.max_workers = max_workers
        self._validate_graph()

    def _validate_graph(self) -> None:
        ids = [stage.stage_id for stage in self.stages]
        if len(ids) != len(set(ids)):
            raise ValueError("stage IDs must be unique")
        known = set(ids)
        for stage in self.stages:
            if stage.stage_id in stage.depends_on:
                raise ValueError(f"stage '{stage.stage_id}' cannot depend on itself")
            unknown = set(stage.depends_on) - known
            if unknown:
                raise ValueError(f"stage '{stage.stage_id}' has unknown dependencies: {sorted(unknown)}")
        remaining = {stage.stage_id: set(stage.depends_on) for stage in self.stages}
        resolved: set[str] = set()
        while remaining:
            ready = [sid for sid, deps in remaining.items() if deps <= resolved]
            if not ready:
                raise ValueError("frontier dependency graph contains a cycle")
            for sid in ready:
                resolved.add(sid)
                del remaining[sid]

    def execute(self) -> ParallelFrontierReceipt:
        observations: dict[str, StageObservation] = {}
        stages = {stage.stage_id: stage for stage in self.stages}

        while len(observations) < len(stages):
            ready = [
                stage for stage in self.stages
                if stage.stage_id not in observations
                and all(dep in observations for dep in stage.depends_on)
            ]
            if not ready:
                raise RuntimeError("frontier could not make progress")

            executable: list[ParallelStage] = []
            for stage in ready:
                blocked_by = [
                    dep for dep in stage.depends_on
                    if observations[dep].status != StageStatus.PASS
                ]
                if blocked_by:
                    observations[stage.stage_id] = StageObservation(
                        stage_id=stage.stage_id,
                        status=StageStatus.BLOCKED,
                        error=f"blocked by failed/incomplete dependency: {blocked_by}",
                    )
                else:
                    executable.append(stage)

            with ThreadPoolExecutor(max_workers=min(self.max_workers, max(1, len(executable)))) as pool:
                futures = {pool.submit(stage.execute): stage for stage in executable}
                for future in as_completed(futures):
                    stage = futures[future]
                    try:
                        output = future.result()
                    except Exception as exc:  # noqa: BLE001 - governed boundary is fail-closed
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
        required_failure = any(
            stage.required and observations[stage.stage_id].status != StageStatus.PASS
            for stage in self.stages
        )
        return ParallelFrontierReceipt(
            frontier_id=self.frontier_id,
            observations=ordered,
            completed_stage_ids=completed,
            failed_stage_ids=failed,
            blocked_stage_ids=blocked,
            verdict=StageStatus.FAILED if required_failure else StageStatus.PASS,
        )
