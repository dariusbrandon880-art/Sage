from sage.experimental.airspace import (
    AirspaceState,
    build_agent_identity,
    render_agent_identity,
    render_agent_nameplate,
    render_chat_nameplate,
)


def test_nameplate_api_is_exported_and_read_only():
    state = AirspaceState()
    station_id = next(iter(state.stations))
    identity = build_agent_identity(state, station_id, state_label="READY")

    assert identity["nameplate"]
    assert identity["station_id"] == station_id.value
    assert identity["read_only"] is True
    assert identity["authority"] == "canonical_airspace_state"
    assert render_agent_nameplate(state, station_id)
    assert render_chat_nameplate(state, station_id).startswith("[SAGE::")
    assert render_agent_identity(state, station_id, state_label="READY").startswith("[SAGE::")
