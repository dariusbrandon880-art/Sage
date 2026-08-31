import pytest

from sage.c2.agent_identity import (
    CHATGPT_AGENT_NAMEPLATE,
    GOOGLE_AGENT_NAMEPLATE,
    JULES_AGENT_NAMEPLATE,
    build_google_nameplate,
)


def test_google_nameplate_is_stable_and_session_bound() -> None:
    identity = build_google_nameplate(session_id="session-google-001")

    assert identity.agent == "GEMINI"
    assert identity.session_id == "session-google-001"
    assert identity.nameplate == GOOGLE_AGENT_NAMEPLATE == "[SAGE::INTEL::GEMINI]"
    assert identity.authority == "governed_runtime_session"


def test_canonical_station_nameplates_are_not_c2_reassigned() -> None:
    assert CHATGPT_AGENT_NAMEPLATE == "[SAGE::C2::CHATGPT]"
    assert JULES_AGENT_NAMEPLATE == "[SAGE::ENGINEER::JULES]"
    assert GOOGLE_AGENT_NAMEPLATE == "[SAGE::INTEL::GEMINI]"
    assert JULES_AGENT_NAMEPLATE != "[SAGE::C2::JULES]"
    assert GOOGLE_AGENT_NAMEPLATE != "[SAGE::C2::GOOGLE]"


def test_google_nameplate_requires_runtime_session() -> None:
    with pytest.raises(ValueError, match="session_id"):
        build_google_nameplate(session_id="")


def test_google_nameplate_rejects_synthetic_flight_identity() -> None:
    with pytest.raises(ValueError, match="Synthetic flight"):
        build_google_nameplate(session_id="FLIGHT_001")
