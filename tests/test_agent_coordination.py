from sage.agent_coordination import (
    C2_REVIEW_ACTIVE,
    COORDINATING,
    ENGINEERING_ACTIVE,
    INTEL_CHALLENGE_ACTIVE,
    STANDBY,
    VERIFYING,
    get_coordination_state,
)
from sage.experimental.airspace.models import AirspaceState, Mission, Sortie, SortieState, StationID


class _FakeManager:
    def __init__(self, state, events):
        self._state = state
        self._events = events

    def reconstruct_airspace_state(self):
        return self._state

    def _load_raw_events(self):
        return self._events


def _patch_coordination(monkeypatch, state, events=None):
    import sage.experimental.airspace.manager as manager_module

    events = events or []
    monkeypatch.setattr(
        manager_module,
        "AirspaceManager",
        lambda: _FakeManager(state, events),
    )


def _state_with_sorties(*sorties):
    state = AirspaceState(
        active_mission=Mission(
            mission_id="mission-test",
            mission_name="Coordination Test",
            theater="Airspace/C2",
            objective="exercise coordination projection",
            assigned_stations=[s.station for s in sorties],
        )
    )
    state.active_sorties = list(sorties)
    return state


def test_no_evidence_of_activity_means_standby(monkeypatch):
    state = AirspaceState()
    _patch_coordination(monkeypatch, state)

    context = get_coordination_state()

    assert context["status"] == STANDBY
    assert context["active_stations"] == []
    assert context["read_only"] is True


def test_intel_active_is_truthfully_challenge_active(monkeypatch):
    sortie = Sortie(
        sortie_id="sortie-intel",
        mission_id="mission-test",
        station=StationID.INTEL_STATION,
        objective="challenge an external claim",
        target="research",
        status=SortieState.ACTIVE,
    )
    _patch_coordination(monkeypatch, _state_with_sorties(sortie))

    context = get_coordination_state()

    assert context["status"] == INTEL_CHALLENGE_ACTIVE
    assert context["stations"]["INTEL_STATION"]["activity"] == INTEL_CHALLENGE_ACTIVE


def test_engineering_active_is_truthfully_engineering(monkeypatch):
    sortie = Sortie(
        sortie_id="sortie-eng",
        mission_id="mission-test",
        station=StationID.ENGINEERING_FLIGHT,
        objective="implement bounded capability",
        target="repository",
        status=SortieState.ACTIVE,
    )
    _patch_coordination(monkeypatch, _state_with_sorties(sortie))

    context = get_coordination_state()

    assert context["status"] == ENGINEERING_ACTIVE
    assert context["stations"]["ENGINEERING_FLIGHT"]["activity"] == ENGINEERING_ACTIVE


def test_c2_active_is_truthfully_review(monkeypatch):
    sortie = Sortie(
        sortie_id="sortie-c2",
        mission_id="mission-test",
        station=StationID.MISSION_CONTROL,
        objective="review implementation evidence",
        target="pull-request",
        status=SortieState.ACTIVE,
    )
    _patch_coordination(monkeypatch, _state_with_sorties(sortie))

    context = get_coordination_state()

    assert context["status"] == C2_REVIEW_ACTIVE
    assert context["stations"]["MISSION_CONTROL"]["activity"] == C2_REVIEW_ACTIVE


def test_evidence_capture_is_verifying(monkeypatch):
    sortie = Sortie(
        sortie_id="sortie-verify",
        mission_id="mission-test",
        station=StationID.ENGINEERING_FLIGHT,
        objective="verify implementation",
        target="tests",
        status=SortieState.EVIDENCE_CAPTURE,
    )
    _patch_coordination(monkeypatch, _state_with_sorties(sortie))

    context = get_coordination_state()

    assert context["status"] == VERIFYING
    assert context["stations"]["ENGINEERING_FLIGHT"]["activity"] == VERIFYING


def test_multiple_active_stations_are_coordination(monkeypatch):
    intel = Sortie(
        sortie_id="sortie-intel",
        mission_id="mission-test",
        station=StationID.INTEL_STATION,
        objective="challenge",
        target="claim",
        status=SortieState.ACTIVE,
    )
    engineering = Sortie(
        sortie_id="sortie-eng",
        mission_id="mission-test",
        station=StationID.ENGINEERING_FLIGHT,
        objective="build",
        target="repository",
        status=SortieState.ACTIVE,
    )
    _patch_coordination(monkeypatch, _state_with_sorties(intel, engineering))

    context = get_coordination_state()

    assert context["status"] == COORDINATING
    assert set(context["active_stations"]) == {"INTEL_STATION", "ENGINEERING_FLIGHT"}


def test_coordination_exposes_event_provenance_without_mutation(monkeypatch):
    state = AirspaceState()
    events = [
        {
            "event_id": "evt-1",
            "event_type": "SORTIE_TRANSITIONED",
            "timestamp": "2026-08-21T20:00:00+00:00",
            "actor": "Jules",
            "mission_id": "mission-test",
            "sortie_id": "sortie-test",
            "evidence_refs": ["test:coordination"],
        }
    ]
    _patch_coordination(monkeypatch, state, events)

    context = get_coordination_state()

    assert context["coordination_event_count"] == 1
    assert context["last_coordination_event"]["event_id"] == "evt-1"
    assert context["last_coordination_event"]["evidence_refs"] == ["test:coordination"]
    assert context["authority"] == "canonical_airspace_state_and_event_ledger"
