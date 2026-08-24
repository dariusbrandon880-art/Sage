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


def test_invalid_identity_rejection():
    """Verify rejection of empty call sign, station ID, or role."""
    import pytest

    with pytest.raises(ValueError, match="call_sign cannot be empty"):
        AgentHUDProjectionEngine.render_identity_badge(
            AgentHUDIdentity(
                call_sign="",
                station_id="ENGINEERING_FLIGHT",
                station_role="Test Lead",
                cql_level=4,
                sql_level=2,
                active_mission_id="Big Strike 001",
                fleet_readiness_status="READY",
                verified_evidence_count=10,
            )
        )

    with pytest.raises(ValueError, match="station_id cannot be empty"):
        AgentHUDProjectionEngine.render_identity_badge(
            AgentHUDIdentity(
                call_sign="Jules",
                station_id="",
                station_role="Test Lead",
                cql_level=4,
                sql_level=2,
                active_mission_id="Big Strike 001",
                fleet_readiness_status="READY",
                verified_evidence_count=10,
            )
        )


def test_negative_evidence_count_rejection():
    """Verify rejection of negative verified evidence count."""
    import pytest

    with pytest.raises(ValueError, match="verified_evidence_count cannot be negative"):
        AgentHUDProjectionEngine.render_identity_badge(
            AgentHUDIdentity(
                call_sign="Jules",
                station_id="ENGINEERING_FLIGHT",
                station_role="Test Lead",
                cql_level=4,
                sql_level=2,
                active_mission_id="Big Strike 001",
                fleet_readiness_status="READY",
                verified_evidence_count=-1,
            )
        )


def test_protected_boundary_isolation():
    """Assert agent_hud_projection does not import protected core namespaces or grant authority."""
    import ast
    from pathlib import Path

    target_file = Path(__file__).parent.parent.parent / "sage" / "experimental" / "agent_hud_projection.py"
    assert target_file.exists()

    file_content = target_file.read_text(encoding="utf-8")
    tree = ast.parse(file_content, filename=str(target_file))

    forbidden = ("sage.runtime", "sage.core", "sage.acr", "sage.agents")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(p) for p in forbidden), f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                assert not any(node.module.startswith(p) for p in forbidden), f"Forbidden import from: {node.module}"
