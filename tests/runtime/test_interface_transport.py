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


def test_chatgpt_client_create_interface_transport():
    from sage.integration import ChatGPTClient

    view = RuntimeView()
    view.state = type("State", (), {"session_id": "session-1"})()
    client = ChatGPTClient(view)

    adapter = client.create_interface_transport("session-1")
    assert isinstance(adapter, InterfaceTransportAdapter)

    observation = InterfaceObservation("session-1", "dom-evt-1", 0, "test telemetry", True)
    projection = adapter.observe(observation)
    assert projection.session_id == "session-1"
    assert projection.station_identity == "[SAGE::C2::CHATGPT]"
    assert projection.immersion["flight_id"] == "C2:session-1"


def test_observation_never_mutates_canonical_runtime_state():
    r = runtime()
    before_digest = r.state.digest()
    view = RuntimeView()
    adapter = InterfaceTransportAdapter(
        r,
        immersion_projector=lambda session_id: build_chatgpt_immersion_state(
            view,
            session_id=session_id,
            c2_context={"active_objective": "Immersion", "active_task": "Verify transport"},
        ),
    )

    adapter.observe(InterfaceObservation("session-1", "dom-2", 1, "untrusted telemetry", True))

    assert r.state.digest() == before_digest
    assert r.state.active_frontier == "chatgpt-boundary"


def test_interface_transport_ingest_jules_report_updates_tower_hud():
    from sage.c2.jules_report_ingestion import JulesReport, compute_hud_projection_key
    from sage.runtime.engine import SageRuntime

    SHA = "e8589d31629feb5ee6a5ea3f44f327f0b2c91885"
    runtime_engine = SageRuntime()
    view = RuntimeView()
    view.canonical_git_sha = SHA

    adapter = InterfaceTransportAdapter(
        runtime_engine,
        immersion_projector=lambda session_id: build_chatgpt_immersion_state(
            view, session_id=session_id, c2_context={"active_objective": "Obj", "active_task": "Task"}
        ),
    )

    hud_proj = {
        "frontier": "live-transport-frontier",
        "gate": "GOVERNED_EXECUTION",
        "flight_id": "F1:transport_flight",
    }
    hud_key = compute_hud_projection_key(hud_proj)

    report = JulesReport.model_validate({
        "session_id": "session-1",
        "report_id": "report-transport-1",
        "git_sha": SHA,
        "branch": "main",
        "status": "VERIFIED",
        "objective": "Verify interface transport HUD update",
        "summary": "Interface transport Jules report ingested.",
        "hud_projection": hud_proj,
        "hud_update_key": hud_key,
    })

    projection = adapter.ingest_jules_report(report, canonical_git_sha=SHA, force_hud=True)

    assert projection.session_id == "session-1"
    assert projection.station_identity == "[SAGE::C2::CHATGPT]"
    assert projection.hud_update_key == hud_key
    assert projection.field_c2_envelope["hud_projection"]["frontier"] == "live-transport-frontier"
    assert "Interface transport Jules report ingested." in projection.rendered_response
    assert "01 — COMMAND BAND // SAGE MISSION CONTROL HUD" in projection.rendered_response


def test_chatgpt_client_rehydrates_c2_context_from_jules_report_memory(tmp_path):
    from sage.c2.jules_report_ingestion import JulesReport, compute_hud_projection_key, ingest_jules_report
    from sage.integration import ChatGPTClient
    from sage.runtime.engine import SageRuntime

    SHA = "e8589d31629feb5ee6a5ea3f44f327f0b2c91885"
    runtime_engine = SageRuntime(str(tmp_path / "sage_data"))

    hud_proj = {
        "frontier": "memory-extracted-frontier",
        "gate": "MEMORY_GATE",
        "flight_id": "F1:mem_flight",
    }
    hud_key = compute_hud_projection_key(hud_proj)

    report = JulesReport.model_validate({
        "session_id": "session-mem-1",
        "report_id": "report-mem-1",
        "git_sha": SHA,
        "branch": "main",
        "status": "VERIFIED",
        "objective": "Verify ChatGPTClient context extraction",
        "summary": "Extract context from report memory.",
        "hud_projection": hud_proj,
        "hud_update_key": hud_key,
    })

    ingest_jules_report(runtime_engine, report, canonical_git_sha=SHA)

    client = ChatGPTClient(runtime_engine)
    context = client._rehydrate_c2_context("session-mem-1")

    assert context["active_frontier"] == "memory-extracted-frontier"
    assert context["gate"] == "MEMORY_GATE"
    assert context["hud_update_key"] == hud_key
    assert context["hud_projection"] == hud_proj
