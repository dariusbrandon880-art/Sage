import pytest

from sage.c2.immersion_rehydration import build_chatgpt_immersion_state
from sage.runtime.interface_transport import (
    CHATGPT_DOM_SURFACE,
    InterfaceObservation,
    InterfaceTransportAdapter,
)
from sage.runtime.model_gateway import SAGEStateSnapshot, SAGERuntime


class RuntimeView:
    def __init__(self):
        self.current_state = type(
            "State",
            (),
            {
                "current_objective": "Immersion",
                "active_task": "Verify transport",
                "blockers": [],
                "dependencies": [],
            },
        )()
        self._status = {"c2_status": {"rehydrated": True}}

    def get_status(self):
        return self._status


def runtime():
    return SAGERuntime(
        SAGEStateSnapshot(
            state_version="1",
            instance_id="sage-instance",
            mission_id="mission-1",
            session_id="session-1",
            authority_scope="director",
            active_frontier="chatgpt-boundary",
            stop_boundary="governance",
        )
    )


def test_observation_is_untrusted_and_projection_is_runtime_derived():
    r = runtime()
    view = RuntimeView()
    adapter = InterfaceTransportAdapter(
        r,
        immersion_projector=lambda session_id: build_chatgpt_immersion_state(
            view,
            session_id=session_id,
            c2_context={"active_objective": "Immersion", "active_task": "Verify transport"},
        ),
    )
    observation = InterfaceObservation("session-1", "dom-1", 0, "model text", True)
    projection = adapter.observe(observation)
    assert observation.origin_boundary == CHATGPT_DOM_SURFACE
    assert projection.station_identity == "[SAGE::C2::CHATGPT]"
    assert projection.immersion["flight_id"] == "C2:session-1"
    assert projection.provenance_head


def test_observation_cannot_switch_canonical_session():
    r = runtime()
    adapter = InterfaceTransportAdapter(
        r,
        immersion_projector=lambda session_id: (_ for _ in ()).throw(AssertionError("must not project")),
    )
    with pytest.raises(ValueError, match="session identity mismatch"):
        adapter.observe(InterfaceObservation("attacker-session", "dom-1", 0, "spoof", True))


def test_command_path_fails_closed_until_governance_callback_exists():
    adapter = InterfaceTransportAdapter(runtime(), immersion_projector=lambda _: pytest.fail("unused"))
    with pytest.raises(ValueError, match="command path is not configured"):
        adapter.authorize_command("session-1", "advance")


def test_authorized_command_is_only_returned_by_explicit_callback():
    seen = []

    def authorize(session_id, command):
        seen.append((session_id, command))
        return "[AUTHORIZED] advance"

    adapter = InterfaceTransportAdapter(
        runtime(),
        immersion_projector=lambda _: pytest.fail("unused"),
        command_authorizer=authorize,
    )
    assert adapter.authorize_command("session-1", "advance") == "[AUTHORIZED] advance"
    assert seen == [("session-1", "advance")]
