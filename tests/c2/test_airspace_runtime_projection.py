from types import SimpleNamespace

from sage.experimental.airspace.models import StationID
from sage.experimental.airspace.runtime_projection import project_runtime_state


def test_runtime_projection_uses_canonical_state_without_inventing_clearance():
    runtime = SimpleNamespace(
        current_state=SimpleNamespace(
            current_objective="Prove governed runtime round-trip",
            active_task="Wire runtime state into Airspace observation",
            blockers=["promotion boundary"],
        ),
        context=SimpleNamespace(session_id="session_test_001"),
    )

    state = project_runtime_state(runtime)

    assert state.session_id == "session_test_001"
    assert state.active_mission is not None
    assert state.active_mission.objective == "Prove governed runtime round-trip"
    assert state.active_mission.current_frontier == "Wire runtime state into Airspace observation"
    assert state.active_mission.constraints == ["BLOCKER: promotion boundary"]
    assert state.current_frontiers == ["Wire runtime state into Airspace observation"]
    assert state.next_clearance == "UNSPECIFIED"
    assert state.active_sorties == []
    assert StationID.MISSION_CONTROL in state.stations


def test_runtime_projection_leaves_missing_runtime_concepts_unbound():
    runtime = SimpleNamespace(
        current_state=SimpleNamespace(
            current_objective=None,
            active_task=None,
            blockers=[],
        ),
        context=None,
    )

    state = project_runtime_state(runtime)

    assert state.active_mission is None
    assert state.current_frontiers == []
    assert state.session_id == "unbound"
    assert state.next_clearance == "UNSPECIFIED"
    assert state.active_sorties == []
