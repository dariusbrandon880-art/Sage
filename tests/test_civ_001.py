"""CIV-001 (Continuity Independence Validation) End-to-End Recovery Tests.

This test suite provides formal verification that SAGE can completely recover, rehydrate,
and resume operation flawlessly from validated persistent logs and snapshots alone,
independent of external session history or conversation memory.
"""

import tempfile
from pathlib import Path

import pytest

from sage.models import ConfidenceLevel, DecisionType, MemoryObject
from sage.runtime import SAGERuntime


@pytest.fixture
def clean_workspace():
    """Provides a temporary, clean workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_civ_001_context_rehydration_and_restoration(clean_workspace):
    """Verify that a fresh runtime successfully recovers all states, databases, and continuity lineage."""
    workspace_1 = clean_workspace / "workspace_alpha"
    workspace_1.mkdir()

    # 1. Initialize SAGE Runtime Alpha
    runtime_alpha = SAGERuntime(str(workspace_1))
    runtime_alpha.start()

    # Set active operational states
    runtime_alpha.set_objective("CIV-001 Verification Objective")
    runtime_alpha.set_task("Verify zero-copy context recovery")
    runtime_alpha.add_blocker("Mock hardware failure simulation")

    # Store memory objects
    mem_obj = MemoryObject(
        object_type="design_pattern",
        content={"pattern_name": "Separation of Concerns", "layers": ["Write", "Read"]},
        tags=["architecture", "civ-001"],
        confidence=ConfidenceLevel.VALIDATED,
    )
    runtime_alpha.memory.store(mem_obj)

    # Record technical decisions with evidence
    decision_id = runtime_alpha.decisions.record_decision(
        decision_type=DecisionType.ARCHITECTURAL,
        description="Split execution pathways to prevent information feedback loops",
        rationale="Enforce Write-Pipeline vs Read-Pipeline strict separation",
        evidence=[mem_obj.id],
    )

    # Build active session & context changes
    assert runtime_alpha.context is not None
    session_id = runtime_alpha.context.session_id

    # Manually link the decision to the session state (matching ingestion pipeline behavior)
    session_state = runtime_alpha.session_manager.retrieve_session(session_id)
    assert session_state is not None
    session_state.add_decision(decision_id)
    runtime_alpha.session_manager.save_session(session_state)

    runtime_alpha.context_tracker.add_recent_change("Simulated validation trace completed")

    # Save Checkpoint & Create Workspace Snapshot (.sage/sage_state.json)
    checkpoint_id = runtime_alpha.checkpoint()
    snapshot_id = runtime_alpha.create_workspace_snapshot()

    assert checkpoint_id is not None
    assert snapshot_id is not None

    # Stop Alpha
    runtime_alpha.stop()

    # --- SIMULATE ENVIRONMENT WIPEOUT & DEPLOYMENT TO NEW ENVIRONMENT ---
    # We create a new workspace Beta, completely empty, representing a new runtime host node
    workspace_beta = clean_workspace / "workspace_beta"
    workspace_beta.mkdir()

    # 2. Initialize SAGE Runtime Beta in a clean environment
    runtime_beta = SAGERuntime(str(workspace_beta))
    runtime_beta.start()

    # Beta starts empty
    assert runtime_beta.current_state.current_objective is None
    assert runtime_beta.current_state.active_task is None
    assert len(runtime_beta.current_state.blockers) == 0
    assert len(runtime_beta.memory.list_all()) == 0
    assert len(runtime_beta.decisions.list_all()) == 0

    # 3. Perform Rehydration (Restore State from the central snapshot registry '.sage/sage_state.json')
    # SAGE v2 uses the central .sage/sage_state.json as its source of truth for continuity rehydration
    restoration_success = runtime_beta.restore_workspace_snapshot(snapshot_id)
    assert restoration_success is True

    # 4. Verify Identity, Objectives, Decisions, and Knowledge are restored independently
    # Active operational state verification
    assert runtime_beta.current_state.current_objective == "CIV-001 Verification Objective"
    assert runtime_beta.current_state.active_task == "Verify zero-copy context recovery"
    assert "Mock hardware failure simulation" in runtime_beta.current_state.blockers

    # Database verification - memory object
    memories_beta = runtime_beta.memory.list_all()
    assert len(memories_beta) == 1
    rehydrated_mem = runtime_beta.memory.retrieve(mem_obj.id)
    assert rehydrated_mem is not None
    assert rehydrated_mem.object_type == "design_pattern"
    assert rehydrated_mem.content["pattern_name"] == "Separation of Concerns"
    assert "civ-001" in rehydrated_mem.tags

    # Database verification - decisions and evidence
    decisions_beta = runtime_beta.decisions.list_all()
    assert len(decisions_beta) == 1
    rehydrated_dec = runtime_beta.decisions.retrieve_decision(decision_id)
    assert rehydrated_dec is not None
    assert rehydrated_dec.decision_type == DecisionType.ARCHITECTURAL
    assert rehydrated_dec.description == "Split execution pathways to prevent information feedback loops"
    assert mem_obj.id in rehydrated_dec.evidence

    # Lineage and Continuity Session Tracker verification
    lineage_beta = runtime_beta.acr.get_lineage()
    assert session_id in lineage_beta

    # Verify structured SessionState restored in SessionStateManager
    session_state_beta = runtime_beta.session_manager.retrieve_session(session_id)
    assert session_state_beta is not None
    assert "CIV-001 Verification Objective" in session_state_beta.active_objectives
    assert decision_id in session_state_beta.important_decisions

    # ContextTracker verification
    current_context = runtime_beta.context_tracker.get_current_context()
    assert current_context is not None
    assert any("Simulated validation trace completed" in chg for chg in current_context.recent_changes)

    # CheckpointManager verification
    checkpoints_beta = runtime_beta.checkpoint_manager.list_all()
    assert len(checkpoints_beta) == 1
    assert checkpoints_beta[0].id == checkpoint_id

    # Self-verification of database integrity in the new node
    integrity_report = runtime_beta.verify_integrity()
    assert integrity_report["is_valid"] is True
    assert integrity_report["lineage_valid"] is True
    assert len(integrity_report["issues"]) == 0

    runtime_beta.stop()
