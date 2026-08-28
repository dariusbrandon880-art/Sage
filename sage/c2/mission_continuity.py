"""Canonical mission hierarchy guardrails for C2 runtime rehydration."""
from __future__ import annotations

from dataclasses import dataclass, field


class MissionContinuityFailure(RuntimeError):
    pass


@dataclass(frozen=True)
class MissionState:
    end_state: str
    main_goals: tuple[str, ...]
    side_goals: tuple[str, ...] = ()
    active_threads: tuple[str, ...] = ()


@dataclass
class RehydrationSnapshot:
    mission: MissionState
    active_prs: tuple[str, ...] = ()
    active_issues: tuple[str, ...] = ()
    active_flights: tuple[str, ...] = ()
    provenance_events: list[tuple[str, str]] = field(default_factory=list)

    def highest_unresolved_goal(self, completed_goals: set[str] | None = None) -> str:
        completed = completed_goals or set()
        for goal in self.mission.main_goals:
            if goal not in completed:
                return goal
        raise MissionContinuityFailure("no unresolved main goal available")


def preserve_provenance(snapshot: RehydrationSnapshot, source: str, payload: str) -> None:
    if not source.strip():
        raise MissionContinuityFailure("source attribution is required")
    if not payload.strip():
        raise MissionContinuityFailure("provenance payload is required")
    snapshot.provenance_events.append((source, payload))


def require_execution_alignment(snapshot: RehydrationSnapshot, target: str) -> None:
    if not target.strip():
        raise MissionContinuityFailure("execution target is required")
    allowed = set(snapshot.mission.main_goals) | set(snapshot.mission.side_goals) | set(snapshot.mission.active_threads)
    if target not in allowed:
        raise MissionContinuityFailure("FAIL_CLOSED: execution target is outside canonical mission state")


def prevent_local_hyperfixation(snapshot: RehydrationSnapshot, completed_goals: set[str], proposed_target: str) -> None:
    highest = snapshot.highest_unresolved_goal(completed_goals)
    if proposed_target != highest and proposed_target not in snapshot.mission.side_goals:
        raise MissionContinuityFailure(
            f"FAIL_CLOSED: proposed target displaced unresolved main goal: {highest}"
        )
