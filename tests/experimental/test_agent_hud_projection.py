"""Unit tests for Agent Identity HUD Projection Subsystem."""

from sage.experimental.agent_hud_projection import (
    AgentHUDIdentity,
    AgentHUDProjectionEngine,
)


def test_agent_hud_identity_rendering():
    """Verify rendering formatted Command Center Identity Badge for Jules."""
    identity = AgentHUDIdentity(
        call_sign="Jules",
        station_id="ENGINEERING_FLIGHT",
        station_role="Engineering Execution & Test Lead",
        cql_level=4,
        sql_level=2,
        active_mission_id="Big Strike: Frontier Intelligence Expansion",
        fleet_readiness_status="READY",
        verified_evidence_count=29,
    )

    badge = AgentHUDProjectionEngine.render_identity_badge(identity)

    assert "SAGE COMMAND CENTER :: JULES" in badge
    assert "Call Sign        : Jules" in badge
    assert "CQL-4 / SQL-2" in badge
    assert "READY" in badge
    assert "29 verified receipts" in badge


def test_agent_hud_chat_greeting_generation():
    """Verify generating rehydrated chat turn header prefix."""
    identity = AgentHUDIdentity(
        call_sign="GPT",
        station_id="MISSION_CONTROL",
        station_role="C2 Synthesis & Operational Coordination",
        cql_level=4,
        sql_level=3,
        active_mission_id="Big Strike 001",
        fleet_readiness_status="READY",
        verified_evidence_count=35,
    )

    greeting = AgentHUDProjectionEngine.generate_chat_greeting(identity)

    assert "SAGE COMMAND CENTER :: GPT" in greeting
    assert "GPT :: Station MISSION_CONTROL active and standing by for C2 flight orders." in greeting
