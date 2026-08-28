import pytest

from sage.c2.mission_continuity import (
    MissionContinuityFailure,
    MissionState,
    RehydrationSnapshot,
    prevent_local_hyperfixation,
    preserve_provenance,
    require_execution_alignment,
)


@pytest.fixture
def snapshot():
    return RehydrationSnapshot(
        mission=MissionState(
            end_state="persistent governed command environment",
            main_goals=("mission continuity", "governed execution", "operator acceptance"),
            side_goals=("super search", "immersion"),
            active_threads=("PR #288", "nameplate HUD"),
        )
    )


def test_highest_unresolved_goal_preserves_main_hierarchy(snapshot):
    assert snapshot.highest_unresolved_goal({"mission continuity"}) == "governed execution"


def test_execution_outside_canonical_state_fails_closed(snapshot):
    with pytest.raises(MissionContinuityFailure, match="outside canonical mission state"):
        require_execution_alignment(snapshot, "random shiny task")


def test_active_thread_is_allowed_without_replacing_main_state(snapshot):
    require_execution_alignment(snapshot, "PR #288")


def test_provenance_requires_explicit_source_and_payload(snapshot):
    with pytest.raises(MissionContinuityFailure, match="source attribution"):
        preserve_provenance(snapshot, "", "Gemini result")
    with pytest.raises(MissionContinuityFailure, match="payload"):
        preserve_provenance(snapshot, "Gemini", "")
    preserve_provenance(snapshot, "Gemini", "PASS")
    assert snapshot.provenance_events == [("Gemini", "PASS")]


def test_local_hyperfixation_cannot_displace_main_goal(snapshot):
    with pytest.raises(MissionContinuityFailure, match="displaced unresolved main goal"):
        prevent_local_hyperfixation(snapshot, set(), "PR #288")


def test_declared_side_goal_can_execute_without_rewriting_mission(snapshot):
    prevent_local_hyperfixation(snapshot, set(), "super search")
