import pytest

from sage.c2.agent_identity import GOOGLE_AGENT_NAMEPLATE, build_google_nameplate


def test_google_nameplate_is_stable_and_session_bound() -> None:
    identity = build_google_nameplate(session_id="session-google-001")

    assert identity.agent == "GOOGLE"
    assert identity.session_id == "session-google-001"
    assert identity.nameplate == GOOGLE_AGENT_NAMEPLATE
    assert identity.authority == "governed_runtime_session"


def test_google_nameplate_requires_runtime_session() -> None:
    with pytest.raises(ValueError, match="session_id"):
        build_google_nameplate(session_id="")


def test_google_nameplate_rejects_synthetic_flight_identity() -> None:
    with pytest.raises(ValueError, match="Synthetic flight"):
        build_google_nameplate(session_id="FLIGHT_001")
