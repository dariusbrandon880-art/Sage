"""Unit and integration tests for SAGE Runtime + Cognitive Integration Bridge."""

from pathlib import Path
import pytest

from sage.experimental.cognitive.prefrontal_cortex import DecisionGateOutcome
from sage.experimental.cognitive.runtime_bridge import RuntimeCognitiveBridge
from sage.integration import AIQueryRequest, GeminiJulesClient
from sage.runtime.engine import SageRuntime


def test_runtime_get_c2_context(tmp_path: Path):
    """Verify RuntimeCognitiveBridge.get_c2_context rehydrates complete operating context."""
    runtime = SageRuntime(str(tmp_path))
    runtime.set_objective("Test C2 Context Objective")
    runtime.set_task("Test C2 Context Task")

    bridge = RuntimeCognitiveBridge(runtime)
    c2_ctx = bridge.get_c2_context("session_test_123")
    assert c2_ctx["c2_identity"] == "SAGE_C2_COMMAND_CENTER"
    assert c2_ctx["session_id"] == "session_test_123"
    assert c2_ctx["rehydrated"] is True
    assert c2_ctx["active_objective"] == "Test C2 Context Objective"
    assert c2_ctx["active_task"] == "Test C2 Context Task"
    assert c2_ctx["governance_status"] == "ACTIVE"
    assert "team_context" in c2_ctx


def test_execute_cognitive_cycle_success(tmp_path: Path):
    """Verify end-to-end continuous cognitive cycle execution and receipt archiving."""
    runtime = SageRuntime(str(tmp_path))
    runtime.set_objective("Execute governed cognitive integration tests")

    bridge = RuntimeCognitiveBridge(runtime)
    result = bridge.execute_cognitive_cycle(
        action_id="act_cog_001",
        description="Execute governed cognitive integration tests action",
        agent_id="MISSION_CONTROL",
        agent_name="C2 Mission Control",
    )

    assert result.success is True
    assert result.action_id == "act_cog_001"
    assert result.pfc_outcome == DecisionGateOutcome.PROCEED
    assert result.cognitive_state_digest is not None
    assert len(result.cognitive_state_digest) == 64
    assert result.progression_receipt_digest is not None
    assert len(result.progression_receipt_digest) == 64
    assert result.archive_entry_id == "ARCHIVE-COG-act_cog_001"

    # Verify Master Archive promotion
    arch_entry = runtime.archive.retrieve_entry("ARCHIVE-COG-act_cog_001")
    assert arch_entry is not None
    assert arch_entry.title == "Cognitive Execution Progression Receipt: act_cog_001"
    assert "c2_progression" in arch_entry.tags

    # Verify state file persisted on disk
    state_path = tmp_path / "cognitive" / "active_state.json"
    assert state_path.exists()


def test_execute_cognitive_cycle_pfc_block_unauthorized_agent(tmp_path: Path):
    """Verify fail-closed behavior when PFC blocks an unauthorized agent."""
    runtime = SageRuntime(str(tmp_path))
    runtime.set_objective("Execute governed cognitive integration tests")

    bridge = RuntimeCognitiveBridge(runtime)
    result = bridge.execute_cognitive_cycle(
        action_id="act_unauth_001",
        description="Execute governed cognitive integration tests action",
        agent_id="UNAUTHORIZED_ROGUE_AGENT",
        agent_name="Rogue Agent",
    )

    assert result.success is False
    assert result.pfc_outcome == DecisionGateOutcome.BLOCK
    assert "not in the operator's authorized agents list" in result.pfc_reason
    assert any("PFC_BLOCK" in blocker for blocker in runtime.current_state.blockers)


def test_gemini_jules_client_c2_rehydration_and_governance(tmp_path: Path):
    """Verify GeminiJulesClient rehydrates C2 context and enforces protocol governance."""
    runtime = SageRuntime(str(tmp_path))
    runtime.set_objective("Gemini Jules C2 Rehydration Objective")

    client = GeminiJulesClient(runtime)

    # Valid response execution with override
    request = AIQueryRequest(
        prompt="Status query for Gemini station",
        response_override=(
            "Deep continuation response from Gemini/Jules station.\n"
            "C2 Operating Context rehydrated successfully.\n"
            "Referenced SAGE keys: []"
        ),
    )
    response = client.execute_query(request)
    assert response.session_id is not None
    assert "Gemini/Jules rehydrated C2 context" in response.reasoning_history[0]

    # Verify memory ingestion
    memories = runtime.memory.list_all()
    gemini_mems = [m for m in memories if "gemini_jules" in m.tags]
    assert len(gemini_mems) > 0

    # Roleplay violation enforcement
    roleplay_request = AIQueryRequest(
        prompt="Roleplay query",
        response_override="*smiles* Hello operator! I am pretending to be your AI character.",
    )
    with pytest.raises(RuntimeError, match="SAGE Protocol Governance Violation"):
        client.execute_query(roleplay_request)
