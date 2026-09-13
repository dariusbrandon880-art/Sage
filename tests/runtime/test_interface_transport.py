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


def test_interface_projection_accepts_field_and_tower_c2_stations():
    from sage.c2.immersion_state import ExecutionPhase, FlightStatus, ImmersionState, TrustStatus
    from sage.runtime.interface_transport import InterfaceProjection

    field_state = ImmersionState(
        station_identity="[SAGE::C2::FIELD]",
        mission="Test Field Mission",
        phase=ExecutionPhase.EXECUTE,
        flight_id="F1:test_001",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.VERIFIED,
        frontier="field-frontier",
        gate="GOVERNED_EXECUTION",
        next_move="Advance",
        provenance_head="e8589d31629feb5ee6a5ea3f44f327f0b2c91885",
    )
    projection = InterfaceProjection.from_immersion("session-1", field_state)
    assert projection.station_identity == "[SAGE::C2::FIELD]"
    assert projection.immersion["frontier"] == "field-frontier"

    tower_state = ImmersionState(
        station_identity="[SAGE::C2::TOWER]",
        mission="Test Tower Mission",
        phase=ExecutionPhase.VERIFY,
        flight_id="F2:test_002",
        flight_status=FlightStatus.COMPLETED,
        trust_status=TrustStatus.VERIFIED,
        frontier="tower-frontier",
        gate="VERIFIED_GATE",
        next_move="Promote",
        provenance_head="e8589d31629feb5ee6a5ea3f44f327f0b2c91885",
    )
    projection_tower = InterfaceProjection.from_immersion("session-1", tower_state)
    assert projection_tower.station_identity == "[SAGE::C2::TOWER]"

    invalid_state = ImmersionState(
        station_identity="[SAGE::UNAUTHORIZED::AGENT]",
        mission="Test Invalid Mission",
        phase=ExecutionPhase.EXECUTE,
        flight_id="F3:test_003",
        flight_status=FlightStatus.ACTIVE,
        trust_status=TrustStatus.UNVERIFIED,
        frontier="invalid-frontier",
        gate="UNAUTHORIZED",
        next_move="Stop",
        provenance_head="e8589d31629feb5ee6a5ea3f44f327f0b2c91885",
    )
    with pytest.raises(ValueError, match="interface projection requires canonical C2 station"):
        InterfaceProjection.from_immersion("session-1", invalid_state)


def test_interface_transport_adapter_ingest_jules_report():
    from sage.c2.jules_report_ingestion import JulesReport, compute_hud_projection_key
    from sage.integration import ChatGPTClient

    SHA = "e8589d31629feb5ee6a5ea3f44f327f0b2c91885"

    class MockMemory:
        def __init__(self):
            self.items = []

        def list_all(self):
            return self.items

    class MockRuntime:
        def __init__(self):
            self.state = type("State", (), {"session_id": "session-1"})()
            self.current_state = type("State", (), {"current_objective": "Bridge Field C2", "active_task": "Adapter test"})()
            self.memory = MockMemory()
            self.payloads = []

        def ingest_session_payload(self, payload):
            self.payloads.append(payload)
            for m in payload.memories:
                m_obj = type("MemItem", (), {
                    "object_type": m["object_type"],
                    "session_id": payload.session_id,
                    "content": m["content"],
                    "tags": m["tags"],
                })()
                self.memory.items.append(m_obj)

        def get_status(self):
            return {"c2_status": {"rehydrated": True}}

    r = MockRuntime()
    client = ChatGPTClient(r)
    adapter = client.create_interface_transport("session-1")

    hud_proj = {
        "frontier": "live-interface-bridge",
        "gate": "GOVERNED_EXECUTION",
        "flight_id": "F1:jules_live_01",
        "phase": "EXECUTE",
        "trust_status": "VERIFIED",
    }
    report = JulesReport.model_validate({
        "session_id": "session-1",
        "report_id": "rep_live_01",
        "git_sha": SHA,
        "branch": "c2/live-bridge",
        "status": "VERIFIED",
        "objective": "Bridge Field C2 to Live Interface",
        "summary": "Field-C2 report ingested live through adapter",
        "hud_projection": hud_proj,
        "hud_update_key": compute_hud_projection_key(hud_proj),
        "session_lineage": ["parent-session", "session-1"],
    })

    projection = adapter.ingest_jules_report(report, canonical_git_sha=SHA, force_hud=True)
    assert projection.session_id == "session-1"
    assert projection.station_identity == "[SAGE::C2::CHATGPT]"
    assert projection.immersion["frontier"] == "live-interface-bridge"
    assert projection.immersion["gate"] == "GOVERNED_EXECUTION"


def test_chatgpt_client_rehydrate_c2_context_extracts_ingested_jules_report():
    from sage.c2.jules_report_ingestion import JulesReport, compute_hud_projection_key, ingest_jules_report
    from sage.integration import ChatGPTClient

    SHA = "e8589d31629feb5ee6a5ea3f44f327f0b2c91885"

    class MockMemory:
        def __init__(self):
            self.items = []

        def list_all(self):
            return self.items

    class MockRuntime:
        def __init__(self):
            self.state = type("State", (), {"session_id": "session-1"})()
            self.current_state = type("State", (), {"current_objective": "Ingest Report Memory", "active_task": "Ingested task"})()
            self.memory = MockMemory()

        def ingest_session_payload(self, payload):
            for m in payload.memories:
                m_obj = type("MemItem", (), {
                    "object_type": m["object_type"],
                    "session_id": payload.session_id,
                    "content": m["content"],
                    "tags": m["tags"],
                })()
                self.memory.items.append(m_obj)

        def get_status(self):
            return {"c2_status": {"rehydrated": True}}

    r = MockRuntime()
    hud_proj = {
        "frontier": "ingested-memory-frontier",
        "gate": "VERIFIED_GATE",
        "flight_id": "F1:ingested_01",
    }
    report = JulesReport.model_validate({
        "session_id": "session-1",
        "report_id": "rep_mem_01",
        "git_sha": SHA,
        "branch": "c2/ingested-memory",
        "status": "VERIFIED",
        "objective": "Ingest Report Memory",
        "summary": "Ingested summary in memory",
        "hud_projection": hud_proj,
        "hud_update_key": compute_hud_projection_key(hud_proj),
        "session_lineage": ["s_0", "session-1"],
    })

    ingest_jules_report(r, report, canonical_git_sha=SHA)

    client = ChatGPTClient(r)
    c2_context = client._rehydrate_c2_context("session-1")
    assert c2_context["active_frontier"] == "ingested-memory-frontier"
    assert c2_context["gate"] == "VERIFIED_GATE"
    assert c2_context["flight_id"] == "F1:ingested_01"
    assert c2_context["active_task"] == "Ingested summary in memory"
    assert c2_context["session_lineage"] == ["s_0", "session-1"]
